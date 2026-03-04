from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import RestaurantOrder, Order

@receiver(post_save, sender=RestaurantOrder)
def order_saved(sender, instance, created, **kwargs):
    """Send WebSocket notification when order is created or updated"""
    channel_layer = get_channel_layer()
    
    order_data = {
        'id': instance.id,
        'items': instance.items,
        'status': instance.status,
        'user': instance.user.username if instance.user else 'Guest',
        'created_at': instance.created_at.isoformat()
    }
    
    if created:
        # New order created
        async_to_sync(channel_layer.group_send)(
            'orders',
            {
                'type': 'order_created',
                'order': order_data
            }
        )
    else:
        # Order updated (status changed)
        async_to_sync(channel_layer.group_send)(
            'orders',
            {
                'type': 'order_update',
                'order': order_data
            }
        )


# ========== ORDER TRACKING SIGNALS ==========

@receiver(pre_save, sender=Order)
def cache_previous_order_status(sender, instance, **kwargs):
    """Cache previous status so post_save can detect transitions accurately."""
    if not instance.pk:
        instance._previous_status = None
        return

    try:
        previous = Order.objects.get(pk=instance.pk)
        instance._previous_status = previous.status
    except Order.DoesNotExist:
        instance._previous_status = None

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """
    Automatically create tracking record when order status changes to 'shipped'.
    Also broadcast tracking updates via WebSocket.
    """
    from .services.logistics_service import LogisticsService, broadcast_tracking_update
    
    previous_status = getattr(instance, '_previous_status', None)
    became_shipped = instance.status == 'shipped' and previous_status != 'shipped'

    if became_shipped:
        tracking = LogisticsService.create_tracking_for_order(instance)
        broadcast_tracking_update(tracking)




