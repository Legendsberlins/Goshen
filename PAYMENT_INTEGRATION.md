# Payment Integration Documentation

This documentation covers the payment integration system for Goshen Giant Food Django app.

## Overview

The payment system supports multiple payment gateways:
- **Stripe**: International credit/debit card payments
- **Paystack**: Nigerian cards, bank transfers, and USSD payments
- **Bank Transfer**: Manual bank transfer option

## Architecture

### Components

1. **Models** (`models.py`)
   - `Order`: Tracks customer orders with delivery info and totals
   - `OrderItem`: Individual line items in an order
   - `Payment`: Payment transaction records with gateway details

2. **Payment Service** (`services/payment_service.py`)
   - Abstract `PaymentGateway` base class
   - `PaymentService`: Routes requests to appropriate gateways
   - Singleton pattern for gateway management

3. **Gateway Implementations**
   - `StripeGateway` (`services/stripe_gateway.py`): Stripe Checkout integration
   - `PaystackGateway` (`services/paystack_gateway.py`): Paystack API integration

4. **Webhook Handlers** (`services/webhooks.py`)
   - Stripe webhook endpoint
   - Paystack webhook endpoint
   - Automatic order status updates on payment confirmation

5. **Views** (`views.py`)
   - `checkout_payment`: Payment method selection and order creation
   - `payment_success`: Payment verification and confirmation
   - `payment_cancel`: Handle cancelled payments

## Installation

### 1. Install Required Packages

```bash
pip install -r requirements-payment.txt
```

Or install individually:
```bash
pip install stripe requests
```

### 2. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Configure Environment Variables

Add these to your environment variables or `.env` file:

```bash
# Site URL (for payment callbacks)
SITE_URL=http://localhost:8000

# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_your_public_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Paystack Configuration
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
```

### 4. Get API Keys

#### Stripe
1. Sign up at https://stripe.com
2. Go to Developers > API keys
3. Copy your publishable and secret keys
4. For webhooks: Developers > Webhooks > Add endpoint
   - URL: `https://yourdomain.com/webhooks/stripe/`
   - Events: `checkout.session.completed`, `payment_intent.succeeded`, `payment_intent.payment_failed`

#### Paystack
1. Sign up at https://paystack.com
2. Go to Settings > API Keys & Webhooks
3. Copy your public and secret keys
4. For webhooks: Add webhook URL
   - URL: `https://yourdomain.com/webhooks/paystack/`

## Usage

### Payment Flow

1. **User adds items to cart** → Session-based cart storage
2. **Checkout address** → User provides delivery address
3. **Choose payment method** → User selects Stripe, Paystack, or Bank Transfer
4. **Create order** → System creates Order and OrderItem records
5. **Redirect to gateway** → User redirected to payment page
6. **Payment completion** → User returns to success page
7. **Webhook verification** → Gateway sends webhook to verify payment
8. **Email confirmation** → System sends order confirmation email

### Testing

#### Stripe Test Cards
```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
```

#### Paystack Test Cards
```
Success: 5060 6666 6666 6666 666, PIN: 123, OTP: 123456
Decline: 5060 0000 0000 0000 006, PIN: 123
```

## Security Features

1. **Webhook Signature Verification**
   - Stripe: HMAC SHA-256 signature verification
   - Paystack: HMAC SHA-512 signature verification

2. **CSRF Protection**
   - Payment forms protected with Django CSRF tokens
   - Webhook endpoints exempt (verified via signatures)

3. **Amount Validation**
   - Order totals calculated server-side
   - Gateway responses verified before marking orders as paid

4. **Transaction ID Storage**
   - All gateway transaction IDs stored for reconciliation
   - Full gateway responses stored in JSON field

## Extending the System

### Adding a New Payment Gateway

1. Create a new gateway class implementing `PaymentGateway`:

```python
# services/new_gateway.py
from .payment_service import PaymentGateway

class NewGateway(PaymentGateway):
    def create_payment_session(self, order, amount, currency='NGN'):
        # Implementation
        pass
    
    def verify_payment(self, reference):
        # Implementation
        pass
    
    def process_webhook(self, payload, signature=None):
        # Implementation
        pass
```

2. Register the gateway in `checkout_payment` view:

```python
from .services.new_gateway import NewGateway

payment_service.register_gateway('new_gateway', NewGateway(api_key))
```

3. Add webhook handler in `services/webhooks.py`

4. Update payment method choices in `Payment` model

## Environment Configuration

### Development
```bash
# Use test API keys
STRIPE_SECRET_KEY=sk_test_...
PAYSTACK_SECRET_KEY=sk_test_...
SITE_URL=http://localhost:8000
```

### Production
```bash
# Use live API keys
STRIPE_SECRET_KEY=sk_live_...
PAYSTACK_SECRET_KEY=sk_live_...
SITE_URL=https://yourdomain.com

# Enable HTTPS
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Webhook URLs

Configure these URLs in your payment gateway dashboards:

- Stripe: `https://yourdomain.com/webhooks/stripe/`
- Paystack: `https://yourdomain.com/webhooks/paystack/`

**Important**: Webhooks must be accessible over HTTPS in production.

## Admin Interface

The Django admin provides management for:

- **Orders**: View all orders, filter by status/payment status
- **Order Items**: Individual line items
- **Payments**: Transaction records with gateway details

Access at: `/admin/`

## Email Notifications

Order confirmation emails are sent automatically when:
- Payment is verified via webhook
- Payment is verified on success page callback

Email template location: `services/email_service.py`

## Troubleshooting

### Payment not marked as paid
- Check webhook configuration in gateway dashboard
- Verify webhook signature secrets match
- Check server logs for webhook errors
- Ensure webhooks accessible over internet (use ngrok for local testing)

### Gateway not available
- Verify API keys in environment variables
- Check `stripe_available` / `paystack_available` in template context
- Ensure packages installed correctly

### Order not created
- Check cart session data
- Verify product prices are set
- Check server logs for errors

## API Reference

### PaymentService Methods

```python
# Create payment session
payment_service.create_payment(
    gateway_name='stripe',  # or 'paystack'
    order=order_instance,
    amount=Decimal('10000.00'),
    currency='NGN'
)

# Verify payment
payment_service.verify_payment(
    gateway_name='stripe',
    reference='session_id_or_reference'
)

# Process webhook
payment_service.process_webhook(
    gateway_name='stripe',
    payload=request.body,
    signature=request.META.get('HTTP_STRIPE_SIGNATURE')
)
```

## Database Schema

### Order Model
- `order_number`: Unique identifier (auto-generated)
- `user`: FK to User (nullable for guest checkout)
- `recipient_name`, `phone`, `address_line`, etc.: Delivery info
- `subtotal`, `shipping_cost`, `total`: Amounts
- `status`: Order status (pending, processing, shipped, delivered)
- `payment_status`: Payment status (pending, paid, failed, refunded)

### Payment Model
- `order`: FK to Order
- `payment_method`: Gateway used
- `amount`, `currency`: Payment amount
- `status`: Payment status
- `gateway_transaction_id`: Gateway's transaction ID
- `gateway_reference`: Payment reference
- `gateway_response`: Full JSON response from gateway

## Support

For issues or questions:
1. Check server logs for error details
2. Verify webhook configuration
3. Test with sandbox/test credentials first
4. Review gateway documentation
