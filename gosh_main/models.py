from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.CharField(max_length=255, blank=True, help_text="Static path under static/ (e.g. 'gosh_main/images/foo.jpg')")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author_name = models.CharField(max_length=200)
    rating = models.PositiveSmallIntegerField(default=5)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author_name} — {self.product.name} ({self.rating})"


class NewsletterSignup(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} <{self.email}>: {self.subject}"


class AboutBlock(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    image = models.CharField(max_length=255, blank=True, help_text="Static path under static/ (e.g. 'gosh_main/images/foo.jpg')")

    def __str__(self):
        return self.title


class Feature(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.CharField(max_length=255, help_text="Static path under static/ (e.g. 'gosh_main/images/features/natural.png')")

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title


class ContactInfo(models.Model):
    organisation = models.CharField(max_length=255, default='Goshen Giant Food')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    extra = models.TextField(blank=True)

    def __str__(self):
        return self.organisation


class Address(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=100, blank=True, help_text='e.g. Home, Office')
    recipient_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    address_line = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label or 'Address'} for {self.user.username}"


class RestaurantOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_orders'
    )
    items = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Restaurant order {self.id} ({self.status})"


class Order(models.Model):
    """Order model to track customer orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Delivery information
    recipient_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    address_line = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')
    
    # Order totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8].upper()
            self.order_number = f'ORD-{timestamp}-{unique_id}'
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)  # Store name in case product is deleted
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        self.line_total = self.product_price * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment transaction model"""
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
        ('paypal', 'PayPal'),
        ('card', 'Direct Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Payment gateway details
    gateway_transaction_id = models.CharField(max_length=255, blank=True, help_text='Transaction ID from payment gateway')
    gateway_reference = models.CharField(max_length=255, blank=True, help_text='Payment reference')
    gateway_response = models.JSONField(blank=True, null=True, help_text='Full response from gateway')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Additional information
    payer_email = models.EmailField(blank=True)
    payer_name = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} for {self.order.order_number} - {self.status}"


class LogisticsCompany(models.Model):
    """Model to store logistics/delivery companies information"""
    
    COUNTRY_CHOICES = [
        ('NG', 'Nigeria'),
        ('US', 'United States'),
        ('UK', 'United Kingdom'),
        ('CA', 'Canada'),
        ('FR', 'France'),
        ('DE', 'Germany'),
        ('IT', 'Italy'),
        ('ES', 'Spain'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='NG')
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    logo = models.CharField(max_length=255, blank=True, help_text="URL or static path to company logo")
    tracking_url = models.URLField(blank=True, help_text="URL template for tracking (e.g., https://company.com/track/)")
    
    # Coverage: JSONField storing list of states/regions they serve
    coverage_states = models.JSONField(
        default=list,
        help_text="List of states/regions covered by this company"
    )
    
    # Pricing info
    base_shipping_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Base shipping cost"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'country']
    
    def __str__(self):
        return f"{self.name} ({self.get_country_display()})"


class OrderTracking(models.Model):
    """Real-time tracking information for orders"""
    
    STATUS_CHOICES = [
        ('warehouse', 'At Warehouse'),
        ('in_transit', 'In Transit'),
        ('arrived_hub', 'Arrived at Hub'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
    ]
    
    # One-to-one relationship with Order
    order = models.OneToOneField(
        'Order',
        on_delete=models.CASCADE,
        related_name='tracking'
    )
    
    # Logistics company assigned
    logistics_company = models.ForeignKey(
        LogisticsCompany,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tracked_orders'
    )
    
    # Tracking details
    tracking_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique tracking number from logistics company"
    )
    
    # Current location
    current_location_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=0,
        help_text="Current latitude of package"
    )
    current_location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=0,
        help_text="Current longitude of package"
    )
    current_location_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable location name"
    )
    
    # Destination location
    destination_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=0,
        help_text="Destination latitude"
    )
    destination_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=0,
        help_text="Destination longitude"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='warehouse'
    )
    
    # Estimated delivery
    estimated_delivery = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Estimated delivery date and time"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Tracking {self.tracking_number} for Order {self.order.order_number}"
    
    @property
    def is_delivered(self):
        return self.status == 'delivered'
    
    @property
    def current_location(self):
        return {
            'lat': float(self.current_location_lat),
            'lng': float(self.current_location_lng),
            'name': self.current_location_name
        }
    
    @property
    def destination_location(self):
        return {
            'lat': float(self.destination_lat),
            'lng': float(self.destination_lng),
        }


class TrackingHistory(models.Model):
    """Historical log of all tracking updates"""
    
    tracking = models.ForeignKey(
        OrderTracking,
        on_delete=models.CASCADE,
        related_name='history'
    )
    
    # Location update
    location_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )
    location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )
    location_name = models.CharField(max_length=255, blank=True)
    
    # Status at this point
    status = models.CharField(
        max_length=20,
        choices=OrderTracking.STATUS_CHOICES,
        default='in_transit'
    )
    
    # Details about the update
    message = models.CharField(
        max_length=255,
        blank=True,
        help_text="Message about this update"
    )
    
    # Timestamp
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name_plural = "Tracking Histories"
    
    def __str__(self):
        return f"Update for {self.tracking.tracking_number} at {self.recorded_at}"