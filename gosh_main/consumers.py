import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import RestaurantOrder

class OrderConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time order updates"""
    
    async def connect(self):
        """Called when WebSocket connection is established"""
        # Join the "orders" group
        self.room_group_name = 'orders'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current orders on connection
        orders = await self.get_all_orders()
        await self.send(text_data=json.dumps({
            'type': 'order_list',
            'orders': orders
        }))
    
    async def disconnect(self, close_code):
        """Called when WebSocket connection is closed"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket (not used in this implementation)"""
        pass
    
    async def order_update(self, event):
        """Receive order update from group and send to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order': event['order']
        }))
    
    async def order_created(self, event):
        """Receive new order notification and send to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'order_created',
            'order': event['order']
        }))
    
    @database_sync_to_async
    def get_all_orders(self):
        """Fetch all orders from database"""
        orders = RestaurantOrder.objects.all().order_by('-created_at')[:20]
        return [
            {
                'id': order.id,
                'items': order.items,
                'status': order.status,
                'user': order.user.username if order.user else 'Guest',
                'created_at': order.created_at.isoformat()
            }
            for order in orders
        ]


class TrackingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time order tracking updates.
    Clients connect to ws://host/ws/tracking/ to receive updates.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Add this connection to the tracking_updates group
        await self.channel_layer.group_add('tracking_updates', self.channel_name)
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to tracking updates',
            'timestamp': __import__('django.utils.timezone', fromlist=['now']).now().isoformat()
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Remove this connection from the group
        await self.channel_layer.group_discard('tracking_updates', self.channel_name)
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket client.
        Expected formats:
        - Subscribe to specific order: {'action': 'subscribe_order', 'order_id': 123}
        - Get tracking info: {'action': 'get_tracking', 'tracking_number': 'TRK-XXXXX'}
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'subscribe_order':
                order_id = data.get('order_id')
                tracking = await self.get_order_tracking(order_id)
                
                if tracking:
                    await self.send(text_data=json.dumps({
                        'type': 'tracking_data',
                        'tracking': self.serialize_tracking(tracking)
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Tracking not found for this order'
                    }))
            
            elif action == 'get_tracking':
                tracking_number = data.get('tracking_number')
                tracking = await self.get_tracking_by_number(tracking_number)
                
                if tracking:
                    await self.send(text_data=json.dumps({
                        'type': 'tracking_data',
                        'tracking': self.serialize_tracking(tracking)
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Tracking number not found'
                    }))
            
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown action: {action}'
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def tracking_update(self, event):
        """
        Receive tracking update from group and send to WebSocket.
        This is called when a tracking update is broadcast to the group.
        """
        # Send the tracking update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'tracking_update',
            'data': {
                'tracking_id': event.get('tracking_id'),
                'tracking_number': event.get('tracking_number'),
                'order_id': event.get('order_id'),
                'order_number': event.get('order_number'),
                'status': event.get('status'),
                'current_location': event.get('current_location'),
                'destination_location': event.get('destination_location'),
                'estimated_delivery': event.get('estimated_delivery'),
                'is_delivered': event.get('is_delivered'),
                'timestamp': __import__('django.utils.timezone', fromlist=['now']).now().isoformat()
            }
        }))
    
    @database_sync_to_async
    def get_order_tracking(self, order_id: int):
        """Fetch tracking for an order from database"""
        from .models import Order
        try:
            order = Order.objects.get(id=order_id)
            return getattr(order, 'tracking', None)
        except Order.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_tracking_by_number(self, tracking_number: str):
        """Fetch tracking by number from database"""
        from .models import OrderTracking
        try:
            return OrderTracking.objects.get(tracking_number=tracking_number)
        except OrderTracking.DoesNotExist:
            return None
    
    @staticmethod
    def serialize_tracking(tracking):
        """Serialize tracking object to JSON-safe dict"""
        from decimal import Decimal
        
        return {
            'id': tracking.id,
            'tracking_number': tracking.tracking_number,
            'order_id': tracking.order.id,
            'order_number': tracking.order.order_number,
            'status': tracking.status,
            'status_display': tracking.get_status_display(),
            'current_location': {
                'lat': float(tracking.current_location_lat),
                'lng': float(tracking.current_location_lng),
                'name': tracking.current_location_name
            },
            'destination_location': {
                'lat': float(tracking.destination_lat),
                'lng': float(tracking.destination_lng)
            },
            'logistics_company': {
                'name': tracking.logistics_company.name if tracking.logistics_company else 'N/A',
                'logo': tracking.logistics_company.logo if tracking.logistics_company else None,
            } if tracking.logistics_company else None,
            'estimated_delivery': tracking.estimated_delivery.isoformat() if tracking.estimated_delivery else None,
            'delivered_at': tracking.delivered_at.isoformat() if tracking.delivered_at else None,
            'is_delivered': tracking.is_delivered,
            'created_at': tracking.created_at.isoformat(),
            'updated_at': tracking.updated_at.isoformat(),
        }