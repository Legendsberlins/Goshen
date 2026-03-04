from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_order_update(order):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = {
        "id": order.id,
        "user_id": order.user_id,
        "items": order.items,
        "status": order.status,
        "created_at": order.created_at.isoformat(),
    }

    async_to_sync(channel_layer.group_send)(
        "orders",
        {
            "type": "order.update",
            "order": payload,
        },
    )
