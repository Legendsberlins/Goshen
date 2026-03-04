# Order Tracking System - Quick Start Guide

## ⚡ Quick Setup (5 minutes)

### 1. Create Database Migrations
```bash
python manage.py makemigrations gosh_main
python manage.py migrate gosh_main
```

### 2. Create Sample Logistics Company
```bash
python manage.py shell
```

```python
from gosh_main.models import LogisticsCompany

# Create a Nigerian logistics company
LogisticsCompany.objects.create(
    name='Swift Logistics Nigeria',
    country='NG',
    phone='+234-800-123-4567',
    email='support@swiftlog.ng',
    coverage_states=['Lagos', 'Ogun', 'Oyo', 'Osun', 'Edo', 'Delta', 'Rivers'],
    base_shipping_cost=1500
)

# Create US logistics
LogisticsCompany.objects.create(
    name='US Express Delivery',
    country='US',
    phone='+1-800-123-4567',
    coverage_states=['NY', 'CA', 'TX'],
    base_shipping_cost=25.00
)

exit()
```

### 3. Set Mapbox Token
Edit your `.env` file or environment:
```
MAPBOX_TOKEN=pk.eyJ1IjoieW91cnVzZXIiLCJhIjoiY2x...
```

Get free token: https://account.mapbox.com/

### 4. Run Development Server
```bash
# Using Daphne (required for WebSockets)
pip install daphne
daphne -b 0.0.0.0 -p 8000 goshen.asgi:application
```

Or with auto-reload:
```bash
python manage.py runserver
# Note: WebSocket won't work, use daphne for development
```

### 5. Access the System
- **Tracking Page**: http://localhost:8000/track/
- **My Orders**: http://localhost:8000/my-orders/tracking/ (requires login)
- **Admin**: http://localhost:8000/admin/

---

## 🧪 Testing the System

### Test 1: Manual Order Tracking
1. Go to Django Admin
2. Create an Order record
3. Click "Add" next to tracking
4. Visit `/track/` and search for the tracking number

### Test 2: Automatic Tracking Creation
1. Create an order in admin
2. Change status to "shipped"
3. Verify TrackingHistory entry is created
4. Go to `/track/` and see automatic tracking data

### Test 3: Real-time Location Update
1. Open `/track/{tracking_number}/` in browser
2. In another tab, go to admin
3. Click OrderTracking entry
4. Update `current_location_lat`, `current_location_lng`, `current_location_name`
5. Change status (e.g., from "warehouse" to "in_transit")
6. Save
7. Back in tracking tab, map should update in real-time (if WebSocket connected)

### Test 4: Search Functionality
```bash
# Test API search
curl "http://localhost:8000/api/tracking/search/?q=TRK"
```

### Test 5: WebSocket Connection
Open browser DevTools (F12) → Console:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tracking/');
ws.onopen = () => {
    ws.send(JSON.stringify({
        action: 'get_tracking',
        tracking_number: 'TRK-20260301-ABC12345'
    }));
};
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## 📊 Admin Interface

### Logistics Companies
- **Path**: Admin → Gosh Main → Logistics Companies
- Add shipping partners
- Configure coverage areas
- Set shipping costs

### Order Tracking
- **Path**: Admin → Gosh Main → Order Tracking
- View all active trackings
- Inline tracking history
- Update locations and status

### Tracking History
- **Path**: Admin → Gosh Main → Tracking Histories
- See all updates for each order
- Filter by status, date, company

---

## 🔗 API Endpoints

### Get Tracking Details
```bash
curl http://localhost:8000/api/tracking/TRK-20260301-ABC12345/
```

**Response:**
```json
{
    "success": true,
    "tracking": {
        "id": 1,
        "tracking_number": "TRK-20260301-ABC12345",
        "order_number": "ORD-20260301000000-ABC12345",
        "status": "in_transit",
        "current_location": {
            "lat": 6.5244,
            "lng": 3.3792,
            "name": "Lagos Hub"
        },
        "destination_location": {
            "lat": 7.3686,
            "lng": 3.9155
        },
        "estimated_delivery": "2026-03-08T00:00:00Z",
        "is_delivered": false
    },
    "history": [...]
}
```

### Update Location (Admin)
```bash
curl -X POST http://localhost:8000/api/tracking/update/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=xxx" \
  -d '{
    "tracking_id": 1,
    "latitude": 6.9271,
    "longitude": 3.7347,
    "location_name": "Ibadan Distribution Center",
    "status": "in_transit",
    "message": "Package in transit to destination"
  }'
```

### Search Tracking
```bash
curl "http://localhost:8000/api/tracking/search/?q=TRK-2026"
```

---

## 📱 Frontend Integration

### Add Tracking Link to Order Confirmation Email
```html
<!-- In order confirmation email template -->
<p>Track your order: <a href="https://yoursite.com/track/{{ tracking_number }}/">{{ tracking_number }}</a></p>
```

### Add Tracking Button to User Dashboard
```html
<!-- In user account page -->
{% if order.tracking %}
    <a href="/track/{{ order.tracking.tracking_number }}/" class="btn btn-primary">
        Track This Order
    </a>
{% endif %}
```

### Add Navigation Link
```html
<!-- In base.html navigation -->
<a href="/track/" class="nav-link">Track Order</a>
<a href="/my-orders/tracking/" class="nav-link">My Shipments</a>
```

---

## 🔧 Configuration Options

### Tracking Settings (settings.py)
```python
TRACKING_SETTINGS = {
    'default_estimated_delivery_days': 7,      # Change default ETAdatabase
    'warehouse_location': {
        'name': 'Goshen Warehouse',
        'lat': 6.5244,      # Warehouse latitude
        'lng': 3.3792,      # Warehouse longitude
    },
    'international_shipping_days': 14,         # International delivery time
}
```

### Map Style Options
Change in `tracking.html`:
```javascript
style: 'mapbox://styles/mapbox/dark-v10',      // Dark themes
style: 'mapbox://styles/mapbox/light-v10',     // Light theme
style: 'mapbox://styles/mapbox/satellite-v9',  // Satellite view
```

---

## 📧 Notification Setup (Optional)

### Send Email on Status Change
Add to `signals.py`:
```python
from django.core.mail import send_mail
from django.template.loader import render_to_string

@receiver(post_save, sender=OrderTracking)
def notify_status_change(sender, instance, **kwargs):
    if instance.order.user:
        context = {
            'order': instance.order,
            'tracking': instance,
        }
        message = render_to_string('emails/tracking_update.html', context)
        send_mail(
            f'Your order {instance.order.order_number} status: {instance.get_status_display()}',
            message,
            'noreply@goshen.com',
            [instance.order.user.email]
        )
```

### Send SMS Notification (Optional)
```python
from django.conf import settings
import requests

def send_sms_update(tracking):
    if not hasattr(settings, 'TWILIO_ACCOUNT_SID'):
        return
    
    # Use Twilio or your SMS provider
    message = f"Your order {tracking.order.order_number} is {tracking.get_status_display()}"
    # ... send SMS to customer phone
```

---

## 🚀 Deployment Checklist

- [ ] Set `DEBUG = False` in settings.py
- [ ] Configure Mapbox token in environment
- [ ] Set up Redis for channel layers
- [ ] Run migrations on production database
- [ ] Run: `python manage.py collectstatic`
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up HTTPS/SSL
- [ ] Update email configuration
- [ ] Test WebSocket connections
- [ ] Create logistics companies in admin
- [ ] Set up backups for OrderTracking data

---

## 🐛 Debugging

### Check WebSocket Connection
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/tracking/');
ws.onopen = () => console.log('✅ Connected');
ws.onerror = (e) => console.log('❌ Error:', e);
ws.onclose = () => console.log('⛔ Closed');
```

### Check Django Logs
```bash
# Enable logging in settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
        'file': {'class': 'logging.FileHandler', 'filename': 'debug.log'},
    },
    'loggers': {
        'gosh_main': {'handlers': ['console', 'file'], 'level': 'DEBUG'},
    },
}
```

### Test Migrations
```bash
python manage.py migrate --plan gosh_main  # Shows planned migrations
python manage.py migrate gosh_main --verbose
```

---

## 📞 Support Commands

### Reset All Tracking Data
```bash
python manage.py shell
from gosh_main.models import OrderTracking, TrackingHistory
OrderTracking.objects.all().delete()
TrackingHistory.objects.all().delete()
```

### Bulk Create Sample Orders
```bash
python manage.py shell
from django.contrib.auth import get_user_model
from gosh_main.models import Order, LogisticsCompany
from gosh_main.services.logistics_service import LogisticsService

user = get_user_model().objects.first()
for i in range(10):
    order = Order.objects.create(
        user=user,
        recipient_name=f'Customer {i}',
        phone='+234800000000',
        address_line='123 Sample St',
        city='Lagos',
        state='Lagos',
        country='Nigeria',
        subtotal=50000,
        total=51500,
        status='shipped'
    )
    print(f"Created {order.order_number}")
```

---

## ✅ What You Can Do Now

1. **Track orders** in real-time with live map updates
2. **Manage logistics** companies and coverage areas
3. **Update locations** from admin panel
4. **Broadcast updates** to customers via WebSocket
5. **View history** of all tracking changes
6. **Search tracking** by number or order number
7. **Monitor ETAs** for deliveries
8. **Support multiple** countries and regions

---

**Next Steps:**
1. Run migrations
2. Create logistics companies
3. Set Mapbox token
4. Start server with Daphne
5. Test tracking on admin
6. Visit `/track/` to see the map

Happy tracking! 🚀
