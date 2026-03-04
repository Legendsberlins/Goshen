# This file contains tracking-related models
# Add these to models.py or import from here

from django.db import models
from django.conf import settings


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
