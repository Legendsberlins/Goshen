from django.urls import path
from django.shortcuts import render
from . import views
from .services import webhooks

app_name = "gosh_main"

urlpatterns = [
    path("", views.home, name="home"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("verify-email/<uidb64>/<token>/", views.verify_email, name="verify_email"),
    path("password-reset/", views.password_reset_request, name="password_reset_request"),
    path("password-reset/<uidb64>/<token>/", views.password_reset_confirm, name="password_reset_confirm"),
    path("about/", views.about, name="about"),
    path("products/", views.products, name="products"),
    path("shop/", views.shop, name="shop"),
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/address/", views.checkout_address, name="checkout_address"),
    path("checkout/payment/", views.checkout_payment, name="checkout_payment"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
    path("webhooks/stripe/", webhooks.stripe_webhook, name="stripe_webhook"),
    path("webhooks/paystack/", webhooks.paystack_webhook, name="paystack_webhook"),
    path("webhooks/flutterwave/", webhooks.flutterwave_webhook, name="flutterwave_webhook"),
    path("contact/", views.contact, name="contact"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("terms/", lambda request: render(request, 'gosh_main/terms.html'), name='terms'),
    path("privacy/", lambda request: render(request, 'gosh_main/privacy.html'), name='privacy'),
    path("orders/", views.order_tracker, name="order_tracker"),
    path("orders/api/", views.orders_api, name="orders_api"),
    path("orders/create/", views.create_order_view, name="create_order"),
    
    # ========== TRACKING ROUTES ==========
    path("track/", views.track_order, name="track_order"),
    path("track/<str:tracking_number>/", views.track_order, name="track_order_number"),
    path("my-orders/tracking/", views.my_orders_tracking, name="my_orders_tracking"),
    path("api/tracking/<str:tracking_number>/", views.tracking_api, name="tracking_api"),
    path("api/tracking/update/", views.update_tracking_location, name="update_tracking_location"),
    path("api/tracking/search/", views.search_tracking, name="search_tracking"),
]
