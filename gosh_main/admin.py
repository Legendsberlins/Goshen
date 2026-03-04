from django.contrib import admin
from django import forms
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.shortcuts import redirect, render
from django.urls import path, reverse

from . import models
from .services.email_service import send_newsletter_email


class NewsletterSendForm(forms.Form):
	subject = forms.CharField(max_length=255)
	message = forms.CharField(widget=forms.Textarea(attrs={"rows": 8}))


@admin.register(models.User)
class UserAdmin(DjangoUserAdmin):
	list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
	search_fields = ("username", "email", "first_name", "last_name")
	ordering = ("username",)


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'price', 'is_featured', 'created_at')
	list_filter = ('category', 'is_featured')
	search_fields = ('name', 'description')


@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('author_name', 'product', 'rating', 'created_at')
	search_fields = ('author_name', 'text')


@admin.register(models.NewsletterSignup)
class NewsletterAdmin(admin.ModelAdmin):
	list_display = ('email', 'created_at')
	change_list_template = 'admin/gosh_main/newslettersignup/change_list.html'

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				'send-newsletter/',
				self.admin_site.admin_view(self.send_newsletter_view),
				name='gosh_main_newslettersignup_send_newsletter',
			),
		]
		return custom_urls + urls

	def changelist_view(self, request, extra_context=None):
		extra_context = extra_context or {}
		extra_context['send_newsletter_url'] = reverse('admin:gosh_main_newslettersignup_send_newsletter')
		return super().changelist_view(request, extra_context=extra_context)

	def send_newsletter_view(self, request):
		if not self.has_view_or_change_permission(request):
			messages.error(request, "You do not have permission to send newsletters.")
			return redirect('admin:gosh_main_newslettersignup_changelist')

		if request.method == 'POST':
			form = NewsletterSendForm(request.POST)
			if form.is_valid():
				subject = form.cleaned_data['subject'].strip()
				message_body = form.cleaned_data['message'].strip()
				recipients = list(
					models.NewsletterSignup.objects.order_by('email').values_list('email', flat=True)
				)

				if not recipients:
					messages.warning(request, 'No newsletter subscribers found.')
					return redirect('admin:gosh_main_newslettersignup_changelist')

				sent_count = send_newsletter_email(subject, message_body, recipients)
				if sent_count == len(recipients):
					messages.success(request, f'Newsletter sent to {sent_count} subscriber(s).')
				else:
					messages.warning(
						request,
						f'Newsletter sent to {sent_count}/{len(recipients)} subscriber(s). Check logs for failures.',
					)
				return redirect('admin:gosh_main_newslettersignup_changelist')
		else:
			form = NewsletterSendForm()

		context = {
			**self.admin_site.each_context(request),
			'title': 'Send newsletter',
			'opts': self.model._meta,
			'form': form,
		}
		return render(request, 'admin/gosh_main/newslettersignup/send_newsletter.html', context)


@admin.register(models.ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'subject', 'created_at')
	search_fields = ('name', 'email', 'subject')


@admin.register(models.AboutBlock)
class AboutBlockAdmin(admin.ModelAdmin):
	list_display = ('title',)


@admin.register(models.ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
	list_display = ('organisation', 'email', 'phone')


@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
	list_display = ('user', 'label', 'recipient_name', 'phone', 'country')
	search_fields = ('user__username', 'recipient_name', 'phone')


# ========== LOGISTICS AND TRACKING ADMIN ==========

@admin.register(models.LogisticsCompany)
class LogisticsCompanyAdmin(admin.ModelAdmin):
	list_display = ('name', 'country', 'phone', 'is_active', 'created_at')
	list_filter = ('country', 'is_active', 'created_at')
	search_fields = ('name', 'phone', 'email')
	readonly_fields = ('created_at', 'updated_at')
	
	fieldsets = (
		('Company Information', {
			'fields': ('name', 'country', 'phone', 'email')
		}),
		('Branding', {
			'fields': ('logo', 'tracking_url')
		}),
		('Coverage & Pricing', {
			'fields': ('coverage_states', 'base_shipping_cost')
		}),
		('Status', {
			'fields': ('is_active',)
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)


class TrackingHistoryInline(admin.TabularInline):
	model = models.TrackingHistory
	extra = 0
	readonly_fields = ('location_lat', 'location_lng', 'location_name', 'status', 'message', 'recorded_at')
	can_delete = False


@admin.register(models.OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
	list_display = ('tracking_number', 'order_number', 'status', 'estimated_delivery', 'is_delivered', 'created_at')
	list_filter = ('status', 'created_at', 'logistics_company')
	search_fields = ('tracking_number', 'order__order_number', 'current_location_name')
	readonly_fields = ('tracking_number', 'created_at', 'updated_at', 'delivered_at', 'is_delivered')
	inlines = [TrackingHistoryInline]
	
	fieldsets = (
		('Order Information', {
			'fields': ('order', 'tracking_number', 'logistics_company')
		}),
		('Current Location', {
			'fields': ('current_location_lat', 'current_location_lng', 'current_location_name')
		}),
		('Destination', {
			'fields': ('destination_lat', 'destination_lng')
		}),
		('Status & Delivery', {
			'fields': ('status', 'estimated_delivery', 'delivered_at', 'is_delivered')
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)
	
	def order_number(self, obj):
		return obj.order.order_number
	order_number.short_description = 'Order Number'
	
	def is_delivered(self, obj):
		return obj.is_delivered
	is_delivered.boolean = True


@admin.register(models.TrackingHistory)
class TrackingHistoryAdmin(admin.ModelAdmin):
	list_display = ('tracking_number', 'status', 'location_name', 'message', 'recorded_at')
	list_filter = ('status', 'recorded_at')
	search_fields = ('tracking__tracking_number', 'location_name', 'message')
	readonly_fields = ('recorded_at',)
	
	def tracking_number(self, obj):
		return obj.tracking.tracking_number
	tracking_number.short_description = 'Tracking Number'


@admin.register(models.RestaurantOrder)
class RestaurantOrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'status', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('id', 'user__username', 'user__email')
	readonly_fields = ('created_at',)


class OrderItemInline(admin.TabularInline):
	model = models.OrderItem
	extra = 0
	readonly_fields = ('product', 'product_name', 'product_price', 'quantity', 'line_total')


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('order_number', 'tracking_number', 'user', 'recipient_name', 'total', 'status', 'payment_status', 'created_at')
	list_filter = ('status', 'payment_status', 'created_at')
	search_fields = ('order_number', 'tracking__tracking_number', 'recipient_name', 'user__username', 'user__email')
	readonly_fields = ('order_number', 'tracking_number', 'created_at', 'updated_at')
	inlines = [OrderItemInline]
	
	fieldsets = (
		('Order Information', {
			'fields': ('order_number', 'tracking_number', 'user', 'status', 'payment_status')
		}),
		('Delivery Details', {
			'fields': ('recipient_name', 'phone', 'address_line', 'city', 'state', 'country')
		}),
		('Amounts', {
			'fields': ('subtotal', 'shipping_cost', 'total')
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at')
		}),
	)

	def tracking_number(self, obj):
		tracking = getattr(obj, 'tracking', None)
		if not tracking:
			return '-'
		return tracking.tracking_number

	tracking_number.short_description = 'Tracking Number'


@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('order', 'product_name', 'quantity', 'product_price', 'line_total')
	search_fields = ('order__order_number', 'product_name')


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('id', 'order', 'payment_method', 'amount', 'status', 'created_at')
	list_filter = ('payment_method', 'status', 'created_at')
	search_fields = ('order__order_number', 'gateway_transaction_id', 'gateway_reference', 'payer_email')
	readonly_fields = ('created_at', 'updated_at', 'completed_at')
	
	fieldsets = (
		('Payment Information', {
			'fields': ('order', 'payment_method', 'status', 'amount', 'currency')
		}),
		('Payer Details', {
			'fields': ('payer_email', 'payer_name')
		}),
		('Gateway Details', {
			'fields': ('gateway_transaction_id', 'gateway_reference', 'gateway_response')
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at', 'completed_at')
		}),
	)

