# Order Tracking Database Schema

## Entity Relationship Diagram

```
┌─────────────────────┐
│      Order          │
├─────────────────────┤
│ PK: id              │
│ order_number        │
│ user_id (FK)        │
│ recipient_name      │
│ address_line        │
│ city                │
│ state               │
│ country             │
│ status              │◄──┐1:1
│ payment_status      │   │
│ created_at          │   │
│ updated_at          │   │
└─────────────────────┘   │
                          │
┌──────────────────────────────────────────┐
│  OrderTracking      (NEW)                │
├──────────────────────────────────────────┤
│ PK: id                                   │
│ FK: order_id (one-to-one, unique)       │
│ FK: logistics_company_id                 │
│ tracking_number (unique)                 │
│ current_location_lat                     │
│ current_location_lng                     │
│ current_location_name                    │
│ destination_lat                          │
│ destination_lng                          │
│ status                                   │
│ estimated_delivery                       │
│ delivered_at                             │
│ created_at                               │
│ updated_at                               │
└──────────────────────────────────────────┘
           │
           │ 1:M
           ▼
┌──────────────────────────────────────────┐
│  TrackingHistory    (NEW)                │
├──────────────────────────────────────────┤
│ PK: id                                   │
│ FK: tracking_id                          │
│ location_lat                             │
│ location_lng                             │
│ location_name                            │
│ status                                   │
│ message                                  │
│ recorded_at                              │
└──────────────────────────────────────────┘

┌─────────────────────┐
│ LogisticsCompany    │
├─────────────────────┤◄──┐M:1
│ PK: id              │   │
│ name (unique)       │   │
│ country             │   │
│ phone               │   │
│ email               │   │
│ logo                │   │
│ tracking_url        │   │
│ coverage_states     │   │
│ base_shipping_cost  │   │
│ is_active           │   │
│ created_at          │   │
│ updated_at          │   │
└─────────────────────┘   │
                          │
                    OrderTracking
```

## Table Structure

### `gosh_main_logisticscompany`

**Purpose:** Manage shipping/logistics partners

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | BigAutoField | PK | Auto-increment |
| name | CharField(255) | UNIQUE, NOT NULL | Company name |
| country | CharField(2) | NOT NULL | Country code: NG, US, UK, CA, FR, DE, IT, ES |
| phone | CharField(20) | NOT NULL | Contact phone number |
| email | EmailField | NULL | Contact email |
| logo | CharField(255) | BLANK | URL or path to logo image |
| tracking_url | URLField | BLANK | Template URL for tracking link |
| coverage_states | JSONField | DEFAULT: [] | List of covered states/regions |
| base_shipping_cost | DecimalField(10,2) | DEFAULT: 0 | Base cost for shipping |
| is_active | BooleanField | DEFAULT: True | Whether company is active |
| created_at | DateTimeField | AUTOSET | Creation timestamp |
| updated_at | DateTimeField | AUTOSET | Last update timestamp |

**Indexes:**
- (name, country) - UNIQUE compound index

**Example Data:**
```json
{
  "id": 1,
  "name": "Swift Logistics Nigeria",
  "country": "NG",
  "phone": "+234-800-123-4567",
  "email": "support@swift.ng",
  "coverage_states": ["Lagos", "Ogun", "Oyo", "Osun"],
  "base_shipping_cost": "1500.00"
}
```

---

### `gosh_main_ordertracking`

**Purpose:** Real-time tracking of orders during transit

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | BigAutoField | PK | Auto-increment |
| order_id | BigAutoField | FK, UNIQUE | One-to-one with Order |
| logistics_company_id | BigAutoField | FK, NULL | Assigned logistics company |
| tracking_number | CharField(100) | UNIQUE, NOT NULL | Generated: TRK-YYYYMMDD-XXXXXXXX |
| current_location_lat | DecimalField(9,6) | DEFAULT: 0 | Current latitude (-90 to 90) |
| current_location_lng | DecimalField(9,6) | DEFAULT: 0 | Current longitude (-180 to 180) |
| current_location_name | CharField(255) | BLANK | Human-readable location |
| destination_lat | DecimalField(9,6) | DEFAULT: 0 | Destination latitude |
| destination_lng | DecimalField(9,6) | DEFAULT: 0 | Destination longitude |
| status | CharField(20) | NOT NULL | warehouse, in_transit, arrived_hub, out_for_delivery, delivered |
| estimated_delivery | DateTimeField | NULL | ETA for delivery |
| created_at | DateTimeField | AUTOSET | Creation time |
| updated_at | DateTimeField | AUTOSET | Last update time |
| delivered_at | DateTimeField | NULL | Actual delivery timestamp |

**Indexes:**
- tracking_number - UNIQUE
- order_id - UNIQUE
- logistics_company_id - FK
- status - For filtering

**Example Data:**
```json
{
  "id": 1,
  "order_id": 10,
  "logistics_company_id": 1,
  "tracking_number": "TRK-20260301-ABC12345",
  "current_location_lat": "6.5244",
  "current_location_lng": "3.3792",
  "current_location_name": "Lagos Warehouse",
  "destination_lat": "7.3686",
  "destination_lng": "3.9155",
  "status": "in_transit",
  "estimated_delivery": "2026-03-08T00:00:00Z"
}
```

---

### `gosh_main_trackinghistory`

**Purpose:** Historical log of all location and status updates

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | BigAutoField | PK | Auto-increment |
| tracking_id | BigAutoField | FK | Reference to OrderTracking |
| location_lat | DecimalField(9,6) | NOT NULL | Location latitude |
| location_lng | DecimalField(9,6) | NOT NULL | Location longitude |
| location_name | CharField(255) | BLANK | Location description |
| status | CharField(20) | NOT NULL | Status at this update |
| message | CharField(255) | BLANK | Update message/note |
| recorded_at | DateTimeField | AUTOSET | Timestamp of update |

**Indexes:**
- tracking_id - FK (composite with recorded_at)
- status - For filtering
- recorded_at - DESC for timeseries

**Example Data:**
```json
[
  {
    "tracking_id": 1,
    "location_lat": "6.5244",
    "location_lng": "3.3792",
    "location_name": "Lagos Warehouse",
    "status": "warehouse",
    "message": "Order received and packed",
    "recorded_at": "2026-03-01T10:00:00Z"
  },
  {
    "tracking_id": 1,
    "location_lat": "6.9271",
    "location_lng": "3.7347",
    "location_name": "Ibadan Distribution Hub",
    "status": "in_transit",
    "message": "In transit",
    "recorded_at": "2026-03-02T14:30:00Z"
  }
]
```

---

## Data Relationships

### Order → OrderTracking (1:1)
- When order status changes to "shipped", tracking is automatically created
- OneToOneField ensures one tracking per order
- Cascading delete: if order deleted, tracking deleted

### OrderTracking → LogisticsCompany (M:1)
- Multiple orders can use same logistics company
- Company information (name, phone, logo) fetched via FK
- If company deleted, tracking set to NULL

### OrderTracking → TrackingHistory (1:M)
- Multiple history entries for each tracking
- History is immutable (read-only) once created
- Cascading delete: if tracking deleted, all history deleted

---

## Status Workflow

```
Order Created (pending)
         ↓
Order Processed (processing)
         ↓
Order Shipped (shipped) → OrderTracking Created
         ↓
Order Status Flow:
         ↓
warehouse (at warehouse)
         ↓
in_transit (on the way)
         ↓
arrived_hub (at distribution hub)
         ↓
out_for_delivery (with delivery person)
         ↓
delivered (delivered) → delivered_at set, Order status = delivered
```

---

## Indexes and Query Optimization

### Primary Indexes
```sql
CREATE INDEX idx_ordertracking_number ON gosh_main_ordertracking(tracking_number);
CREATE INDEX idx_ordertracking_order ON gosh_main_ordertracking(order_id);
CREATE INDEX idx_ordertracking_status ON gosh_main_ordertracking(status);
CREATE INDEX idx_ordertracking_company ON gosh_main_ordertracking(logistics_company_id);

CREATE INDEX idx_history_tracking ON gosh_main_trackinghistory(tracking_id, recorded_at DESC);
CREATE INDEX idx_history_status ON gosh_main_trackinghistory(status);

CREATE INDEX idx_logistics_country ON gosh_main_logisticscompany(country);
CREATE INDEX idx_logistics_active ON gosh_main_logisticscompany(is_active);
```

### Query Examples

**Find tracking by number (fast):**
```python
tracking = OrderTracking.objects.get(tracking_number='TRK-20260301-ABC12345')
# Uses: idx_ordertracking_number
```

**Get all in-transit shipments (fast):**
```python
trackings = OrderTracking.objects.filter(status='in_transit')
# Uses: idx_ordertracking_status
```

**Get tracking history for order (fast):**
```python
history = tracking.history.all().order_by('-recorded_at')[:10]
# Uses: idx_history_tracking with descending order
```

**Find companies in Nigeria (fast):**
```python
companies = LogisticsCompany.objects.filter(country='NG', is_active=True)
# Uses: idx_logistics_country, idx_logistics_active
```

---

## Data Types and Constraints

### Latitude/Longitude
- **Type:** DecimalField(max_digits=9, decimal_places=6)
- **Range:** Lat (-90, 90), Lng (-180, 180)
- **Precision:** ±0.000001° ≈ ±11cm accuracy
- **Example:** 6.524400, 3.379200

### Status Choices
```python
STATUS_CHOICES = [
    ('warehouse', 'At Warehouse'),
    ('in_transit', 'In Transit'),
    ('arrived_hub', 'Arrived at Hub'),
    ('out_for_delivery', 'Out for Delivery'),
    ('delivered', 'Delivered'),
]
```

### Country Codes (ISO 3166-1 Alpha-2)
```
NG = Nigeria
US = United States
UK = United Kingdom
CA = Canada
FR = France
DE = Germany
IT = Italy
ES = Spain
```

---

## Sample Queries

### Get order with tracking info
```python
order = Order.objects.get(id=1)
tracking = order.tracking  # OneToOne access

print(f"Order: {order.order_number}")
print(f"Tracking: {tracking.tracking_number}")
print(f"Status: {tracking.get_status_display()}")
print(f"Location: {tracking.current_location_name}")
```

### Get all deliveries in last 7 days
```python
from datetime import timedelta
from django.utils import timezone

recent = OrderTracking.objects.filter(
    status='delivered',
    delivered_at__gte=timezone.now() - timedelta(days=7)
).select_related('order', 'logistics_company')

for tracking in recent:
    print(f"{tracking.order_number}: {tracking.logistics_company.name}")
```

### Get tracking history for order
```python
tracking = OrderTracking.objects.get(tracking_number='TRK-XXX')
history = tracking.history.all().order_by('-recorded_at')

for entry in history:
    print(f"{entry.recorded_at}: {entry.status} - {entry.message}")
```

### Find stuck shipments (in transit for >7 days)
```python
from datetime import timedelta
from django.utils import timezone

stuck = OrderTracking.objects.filter(
    status__in=['in_transit', 'arrived_hub'],
    created_at__lt=timezone.now() - timedelta(days=7)
).select_related('logistics_company')

for tracking in stuck:
    print(f"⚠️ {tracking.tracking_number} stuck for 7+ days")
```

---

## Backup and Migration Considerations

### Backup What You Need
- **Critical:** OrderTracking records (tracking numbers and customer data)
- **Critical:** TrackingHistory (audit trail)
- **Important:** LogisticsCompany (company details)

### Before Major Updates
```bash
# Backup data
python manage.py dumpdata gosh_main > backup_tracking.json

# Check migrations
python manage.py showmigrations gosh_main

# Make migrations safely
python manage.py makemigrations --dry-run gosh_main
```

### After Adding New Fields
```bash
# Create migration
python manage.py makemigrations gosh_main

# Test on staging
python manage.py migrate gosh_main --plan

# Apply on production
python manage.py migrate gosh_main
```

---

## Statistics and Monitoring

### Query counts for dashboard
```python
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
week_ago = today - timedelta(days=7)

stats = {
    'total_orders_tracked': OrderTracking.objects.count(),
    'delivered_today': OrderTracking.objects.filter(
        status='delivered',
        delivered_at__date=today
    ).count(),
    'in_transit': OrderTracking.objects.filter(
        status='in_transit'
    ).count(),
    'total_updates': TrackingHistory.objects.count(),
    'avg_delivery_days': (
        OrderTracking.objects.filter(
            status='delivered'
        ).extra(
            select={'days': 'AVG(CAST(delivered_at - created_at AS INTEGER))'}
        ).values('days')[0]
    ),
}
```

---

This schema supports:
- ✅ Real-time location tracking
- ✅ Complete audit trail
- ✅ Multi-country operations
- ✅ Performance at scale (indexes)
- ✅ Data integrity (ForeignKeys)
- ✅ Historical analysis
- ✅ WebSocket broadcasts
