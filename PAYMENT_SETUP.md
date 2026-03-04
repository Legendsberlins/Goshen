# Payment Integration Setup Guide

## Overview
Your Django e-commerce app now supports 4 payment methods:
1. **Credit/Debit Card** (Stripe) - International payments
2. **Flutterwave** - Nigerian & African payments with multiple options
3. **PayPal** - International payments (via Flutterwave)
4. **Bank Transfer** - Manual payment option

## Installation

### 1. Install Required Packages
```bash
pip install stripe requests
```

Or use the requirements file:
```bash
pip install -r requirements-payment.txt
```

### 2. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Configuration

### Environment Variables
Add these to your `.env` file or environment:

```env
# Site URL (required for payment callbacks)
SITE_URL=http://localhost:8000

# Stripe Configuration (Optional - leave empty for test mode)
STRIPE_PUBLIC_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Paystack Configuration (Optional - for Nigerian payments)
PAYSTACK_PUBLIC_KEY=pk_test_your_key_here
PAYSTACK_SECRET_KEY=sk_test_your_key_here

# Flutterwave Configuration (Optional - for African payments)
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST-your_key_here
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-your_key_here
```

### Test Mode
If API keys are not configured, the system will still show all payment options but display configuration messages when users try to pay. This allows you to test the UX without actual payment gateway accounts.

## Getting API Keys

### Stripe (International Cards)
1. Sign up at https://stripe.com
2. Go to Developers → API keys
3. Copy your publishable and secret keys
4. For webhooks: Developers → Webhooks → Add endpoint
   - URL: `https://yourdomain.com/webhooks/stripe/`
   - Events to select: `checkout.session.completed`, `payment_intent.succeeded`, `payment_intent.payment_failed`

### Paystack (Nigerian Payments)
1. Sign up at https://paystack.com
2. Go to Settings → API Keys & Webhooks
3. Copy your public and secret keys
4. For webhooks: Add webhook URL
   - URL: `https://yourdomain.com/webhooks/paystack/`

### Flutterwave (African Payments)
1. Sign up at https://flutterwave.com
2. Go to Settings → API
3. Copy your public and secret keys
4. For webhooks: Settings → Webhooks
   - URL: `https://yourdomain.com/webhooks/flutterwave/`

## Testing

### Test Cards

**Stripe Test Cards:**
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Any future expiry date, any 3-digit CVV

**Paystack Test Cards:**
- Success: `5060 6666 6666 6666 6666`
- PIN: `1234`
- OTP: `123456`

**Flutterwave Test Cards:**
- Success: `5531 8866 5214 2950`
- CVV: `564`
- PIN: `3310`
- OTP: `12345`

### Testing the Flow
1. Add items to cart
2. Proceed to checkout
3. Enter delivery address
4. Select payment method
5. Complete payment with test cards above
6. Verify order appears in admin panel

## Admin Panel

Access the admin panel at `/admin/` to:
- View all orders
- Check payment status
- See transaction details
- Manage order fulfillment

The admin has dedicated sections for:
- **Orders**: View all customer orders with payment status
- **Order Items**: Individual items in each order  
- **Payments**: Payment transaction records with gateway details

## Webhooks

Webhooks are secure endpoints that payment gateways call to notify you of payment events. They ensure payment status is updated even if the customer closes their browser.

### Local Testing with ngrok
For local development, use ngrok to expose your local server:
```bash
ngrok http 8000
```

Then use the ngrok URL for webhook endpoints in your gateway dashboards.

### Production Webhooks
In production, make sure your webhook URLs are:
- HTTPS (required by all gateways)
- Publicly accessible
- Respond quickly (< 5 seconds)

## Security Notes

1. **Never commit API keys** - Use environment variables
2. **Validate webhook signatures** - Already implemented in the code
3. **Verify payment amounts** - System validates order totals match payment amounts
4. **Use HTTPS in production** - Required for payment gateways
5. **Monitor failed payments** - Check admin panel regularly

## Email Notifications

The system automatically sends confirmation emails when:
- Payment is successful (via webhook)
- Order is created with bank transfer

Configure email settings in `settings.py` (already done).

## Customization

### Adding More Payment Gateways
1. Create a new gateway class in `gosh_main/services/`
2. Implement the `PaymentGateway` interface
3. Register in `checkout_payment` view
4. Add webhook handler in `services/webhooks.py`
5. Update template with new option

### Changing Shipping Cost
Edit the `checkout_payment` view:
```python
shipping_cost = Decimal('1000')  # Change this value
```

### Bank Transfer Details
Edit the bank details in `checkout_payment` view:
```python
'bank_details': {
    'bank_name': 'Your Bank',
    'account_number': 'Your Account',
    'account_name': 'Your Business Name'
}
```

## Troubleshooting

**Problem: Payment options not showing**
- Check if you're on the checkout payment page
- Verify templates are loading correctly

**Problem: Payment fails immediately**
- Check API keys are correct in environment
- Verify internet connectivity
- Check Django logs for error details

**Problem: Webhook not firing**
- Verify webhook URL is correct in gateway dashboard
- Check if URL is publicly accessible
- Look for webhook signature errors in logs

**Problem: Order created but payment pending**
- This is normal - webhook will update status
- Check gateway dashboard for payment status
- Manually verify payment in admin if needed

## Support

For issues with:
- **Stripe**: https://support.stripe.com
- **Paystack**: https://support.paystack.com  
- **Flutterwave**: https://support.flutterwave.com

For code issues, check the Django logs and ensure all migrations are applied.
