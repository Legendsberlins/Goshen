"""
Logistics and tracking service for managing order deliveries.
Handles assignment of logistics companies, location updates, and tracking information.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from ..models import Order, OrderTracking, TrackingHistory, LogisticsCompany


class LogisticsService:
    """Service for managing logistics and order tracking"""
    
    # Dictionary mapping Nigerian states to approximate coordinates
    NIGERIAN_STATES_COORDS = {
        'Lagos': {'lat': 6.5244, 'lng': 3.3792},
        'Ogun': {'lat': 6.7638, 'lng': 3.3644},
        'Abeokuta': {'lat': 6.7975, 'lng': 3.3291},
        'Ibadan': {'lat': 7.3686, 'lng': 3.9155},
        'Oyo': {'lat': 7.8367, 'lng': 3.9474},
        'Osun': {'lat': 7.6515, 'lng': 4.5198},
        'Oshogbo': {'lat': 7.7608, 'lng': 4.5598},
        'Ekiti': {'lat': 7.6209, 'lng': 5.2878},
        'Ado-Ekiti': {'lat': 7.6247, 'lng': 5.2242},
        'Kwara': {'lat': 8.8953, 'lng': 4.5491},
        'Ilorin': {'lat': 8.4955, 'lng': 4.5418},
        'Niger': {'lat': 9.1732, 'lng': 6.0095},
        'Minna': {'lat': 9.6159, 'lng': 6.5159},
        'Plateau': {'lat': 9.1765, 'lng': 9.7949},
        'Jos': {'lat': 9.9241, 'lng': 8.8944},
        'Nasarawa': {'lat': 8.5357, 'lng': 8.3697},
        'Kaduna': {'lat': 10.5054, 'lng': 7.4314},
        'Kano': {'lat': 12.0022, 'lng': 8.6753},
        'Katsina': {'lat': 12.9857, 'lng': 7.6172},
        'Zamfara': {'lat': 11.8955, 'lng': 5.5160},
        'Kebbi': {'lat': 12.4531, 'lng': 4.1976},
        'Sokoto': {'lat': 13.0116, 'lng': 5.2406},
        'Borno': {'lat': 11.8528, 'lng': 11.5021},
        'Maiduguri': {'lat': 11.8410, 'lng': 13.1577},
        'Yobe': {'lat': 11.9273, 'lng': 11.9653},
        'Damaturu': {'lat': 11.7614, 'lng': 11.9657},
        'Bauchi': {'lat': 10.3158, 'lng': 9.8441},
        'Gombe': {'lat': 10.2897, 'lng': 11.1784},
        'Adamawa': {'lat': 9.2077, 'lng': 12.4519},
        'Yola': {'lat': 9.2143, 'lng': 12.4845},
        'Taraba': {'lat': 8.7832, 'lng': 11.3929},
        'Jalingo': {'lat': 8.8900, 'lng': 11.3920},
        'Edo': {'lat': 6.5354, 'lng': 5.6471},
        'Benin City': {'lat': 6.3350, 'lng': 5.6201},
        'Delta': {'lat': 5.8520, 'lng': 5.7379},
        'Warri': {'lat': 5.5141, 'lng': 5.7500},
        'Rivers': {'lat': 4.7957, 'lng': 6.9790},
        'Port Harcourt': {'lat': 4.7527, 'lng': 7.0007},
        'Bayelsa': {'lat': 4.9447, 'lng': 6.2642},
        'Yenagoa': {'lat': 4.9464, 'lng': 6.2642},
        'Cross River': {'lat': 6.7137, 'lng': 8.6500},
        'Calabar': {'lat': 5.0379, 'lng': 8.3531},
        'Akwa Ibom': {'lat': 5.0272, 'lng': 7.9135},
        'Uyo': {'lat': 5.0269, 'lng': 7.9113},
        'Abia': {'lat': 5.3935, 'lng': 7.3004},
        'Aba': {'lat': 5.1066, 'lng': 7.3676},
        'Enugu': {'lat': 6.4381, 'lng': 7.5244},
        'Ebonyi': {'lat': 6.3157, 'lng': 8.1050},
        'Abakaliki': {'lat': 6.3219, 'lng': 8.1155},
        'Imo': {'lat': 5.4833, 'lng': 7.0333},
        'Owerri': {'lat': 5.4838, 'lng': 7.0339},
        'Anambra': {'lat': 6.1553, 'lng': 7.0398},
        'Onitsha': {'lat': 6.1539, 'lng': 6.7844},
        'Awka': {'lat': 6.2158, 'lng': 7.0732},
    }
    
    # International country capitals/major cities
    INTERNATIONAL_CITIES = {
        'US': {'lat': 40.7128, 'lng': -74.0060, 'name': 'New York'},  # Default to NY
        'UK': {'lat': 51.5074, 'lng': -0.1278, 'name': 'London'},
        'CA': {'lat': 43.6629, 'lng': -79.3957, 'name': 'Toronto'},
        'FR': {'lat': 48.8566, 'lng': 2.3522, 'name': 'Paris'},
        'DE': {'lat': 52.5200, 'lng': 13.4050, 'name': 'Berlin'},
        'IT': {'lat': 41.9028, 'lng': 12.4964, 'name': 'Rome'},
        'ES': {'lat': 40.4168, 'lng': -3.7038, 'name': 'Madrid'},
    }
    
    @staticmethod
    def get_location_by_state(state: str, country: str = 'Nigeria') -> dict:
        """
        Get approximate coordinates for a given state/city.
        Returns dict with lat, lng, and name keys.
        """
        if country == 'Nigeria' or country == 'NG':
            for state_name, coords in LogisticsService.NIGERIAN_STATES_COORDS.items():
                if state.lower() in state_name.lower() or state_name.lower() in state.lower():
                    return {'lat': coords['lat'], 'lng': coords['lng'], 'name': state_name}
            # Default to Lagos if state not found
            return {'lat': 6.5244, 'lng': 3.3792, 'name': 'Lagos (Default)'}
        else:
            # For international, use the country code
            country_code = country[:2].upper()
            if country_code in LogisticsService.INTERNATIONAL_CITIES:
                city_info = LogisticsService.INTERNATIONAL_CITIES[country_code]
                return {'lat': city_info['lat'], 'lng': city_info['lng'], 'name': city_info['name']}
            # Default to US
            return {'lat': 40.7128, 'lng': -74.0060, 'name': 'New York'}
    
    @staticmethod
    def assign_logistics_company(order: Order) -> LogisticsCompany:
        """
        Automatically assign the nearest/most suitable logistics company
        based on the order's destination state/country.
        
        Priority:
        1. Check if company serves the destination state/country
        2. If multiple companies, choose by proximity/availability
        3. Default to any active company that serves the country
        """
        destination_state = order.state or order.city
        destination_country = order.country
        
        # For Nigeria, look for companies covering the specific state
        if destination_country.upper() in ['NG', 'NIGERIA']:
            companies = LogisticsCompany.objects.filter(
                is_active=True,
                country='NG'
            )
            
            # Try to find a company that covers this state
            for company in companies:
                if destination_state and destination_state in company.coverage_states:
                    return company
            
            # If no specific match, return first active Nigerian company
            company = companies.first()
            if company:
                return company
        else:
            # For international destinations, match by country code
            country_code = destination_country[:2].upper()
            company = LogisticsCompany.objects.filter(
                is_active=True,
                country=country_code
            ).first()
            
            if company:
                return company
        
        # Fallback: return any active company
        return LogisticsCompany.objects.filter(is_active=True).first()
    
    @staticmethod
    def create_tracking_for_order(order: Order) -> OrderTracking:
        """
        Create tracking record for an order.
        Called when order is marked as 'shipped'.
        """
        # Check if tracking already exists
        if hasattr(order, 'tracking') and order.tracking:
            return order.tracking
        
        # Assign logistics company
        logistics_company = LogisticsService.assign_logistics_company(order)
        
        # Get warehouse location (default to Lagos for Nigeria)
        warehouse_location = LogisticsService.get_location_by_state(
            'Lagos',
            'NG' if order.country.upper() in ['NG', 'NIGERIA'] else order.country
        )
        
        # Get destination location
        destination_location = LogisticsService.get_location_by_state(
            order.state or order.city,
            order.country
        )
        
        # Generate unique tracking number
        tracking_number = LogisticsService.generate_tracking_number()
        
        # Create tracking record
        tracking = OrderTracking.objects.create(
            order=order,
            logistics_company=logistics_company,
            tracking_number=tracking_number,
            current_location_lat=warehouse_location['lat'],
            current_location_lng=warehouse_location['lng'],
            current_location_name=f"Warehouse ({warehouse_location['name']})",
            destination_lat=destination_location['lat'],
            destination_lng=destination_location['lng'],
            status='warehouse',
            estimated_delivery=timezone.now() + timedelta(days=7)  # Estimate 7 days
        )
        
        # Create initial history entry
        TrackingHistory.objects.create(
            tracking=tracking,
            location_lat=warehouse_location['lat'],
            location_lng=warehouse_location['lng'],
            location_name=f"Warehouse ({warehouse_location['name']})",
            status='warehouse',
            message='Order received and packed at warehouse'
        )
        
        return tracking
    
    @staticmethod
    def generate_tracking_number() -> str:
        """Generate a unique tracking number"""
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f'TRK-{timestamp}-{unique_id}'
    
    @staticmethod
    def update_location(
        tracking: OrderTracking,
        latitude: float,
        longitude: float,
        location_name: str,
        status: str,
        message: str = ''
    ) -> TrackingHistory:
        """
        Update the location and status of a package.
        Creates a history entry and sends WebSocket notification.
        """
        # Update the tracking record
        tracking.current_location_lat = latitude
        tracking.current_location_lng = longitude
        tracking.current_location_name = location_name
        tracking.status = status
        
        # Set delivered_at if delivered
        if status == 'delivered':
            tracking.delivered_at = timezone.now()
            # Also update order status
            order = tracking.order
            order.status = 'delivered'
            order.save(update_fields=['status', 'updated_at'])
        
        tracking.save(update_fields=[
            'current_location_lat', 'current_location_lng',
            'current_location_name', 'status', 'delivered_at', 'updated_at'
        ])
        
        # Create history entry
        history = TrackingHistory.objects.create(
            tracking=tracking,
            location_lat=latitude,
            location_lng=longitude,
            location_name=location_name,
            status=status,
            message=message or f'Package {status.replace("_", " ").title()}'
        )
        
        return history
    
    @staticmethod
    def get_tracking_by_order(order: Order) -> OrderTracking:
        """Get tracking information for an order"""
        return getattr(order, 'tracking', None)
    
    @staticmethod
    def get_tracking_by_number(tracking_number: str) -> OrderTracking:
        """Fetch tracking by tracking number"""
        return OrderTracking.objects.filter(tracking_number=tracking_number).first()


def broadcast_tracking_update(tracking: OrderTracking):
    """
    Broadcast tracking update via WebSocket.
    Called whenever a tracking record is updated.
    This connects to the tracking consumer.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    # Prepare the update message
    message = {
        'type': 'tracking_update',
        'tracking_id': tracking.id,
        'tracking_number': tracking.tracking_number,
        'order_id': tracking.order.id,
        'order_number': tracking.order.order_number,
        'status': tracking.status,
        'current_location': tracking.current_location,
        'destination_location': tracking.destination_location,
        'estimated_delivery': tracking.estimated_delivery.isoformat() if tracking.estimated_delivery else None,
        'is_delivered': tracking.is_delivered,
    }
    
    # Broadcast to all tracking room consumers
    async_to_sync(channel_layer.group_send)(
        'tracking_updates',
        message
    )
