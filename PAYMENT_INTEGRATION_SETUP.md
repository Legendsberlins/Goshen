# Complete Payment Integration Setup Guide

You now have **4 payment methods** integrated into your Django app:
1. **Stripe** - International credit/debit cards
2. **Flutterwave** - Cards, Bank Transfers, USSD, Mobile Money
3. **Paystack** - Nigerian cards and bank transfers
4. **Bank Transfer** - Manual payment instructions

## Quick Start (5 Simple Steps)

### Step 1: Install Required Packages
```bash
pip install stripe requests
```

### Step 2: Get API Keys

**For Stripe (International Cards):**
1. Go to https://dashboard.stripe.com (sign up if needed)
2. Click "Developers" → "API Keys"
3. Copy your **Secret Key** (starts with `sk_test_` or `sk_live_`)
4. Copy your **Publishable Key** (starts with `pk_test_` or `pk_live_`)
5. (Optional) Go to "Webhooks" to set up webhook for live updates

**For Flutterwave (African Payments):**
1. Go to https://dashboard.flutterwave.com (sign up if needed)
2. Click "Settings" → "API" or "Developers"
3. Copy your **Secret Key** (starts with `FLWSECK_`)
4. Copy your **Public Key** (starts with `FLWPUBK_`)

**For Paystack (Nigerian Payments):**
1. Go to https://dashboard.paystack.com (sign up if needed)
2. Click "Settings" → "Developers"
3. Copy your **Secret Key** (starts with `sk_test_` or `sk_live_`)
4. Copy your **Public Key** (starts with `pk_test_` or `pk_live_`)

### Step 3: Update Your `.env` File
Add these keys to your `.env` file:

```env
# Stripe
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Flutterwave
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST-xxxxx
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-xxxxx

# Paystack
PAYSTACK_PUBLIC_KEY=pk_test_xxxxx
PAYSTACK_SECRET_KEY=sk_test_xxxxx

# Site URL (important for payment callbacks)
SITE_URL=http://localhost:8000
# For production: SITE_URL=https://yourdomain.com
```

### Step 4: Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Test the Payment Options
1. Go to your checkout page
2. You should now see 4 payment options:
   - **Stripe** (Credit/Debit Card)
   - **Flutterwave** (Card, Bank, USSD)
   - **Paystack** (Nigerian Cards & Bank)
   - **Bank Transfer** (Manual)

## Testing Payment Gateways

### Stripe Test Cards
```
Card Number: 4242 4242 4242 4242
Expiry: 12/25
CVV: 123
```

### Flutterwave Test Card
```
Card: 5531 8866 5214 2950
Expiry: 09/32
CVV: 564
```

### Paystack Test Card
```
Card: 5399 8400 0000 0000
Expiry: 09/32
CVV: 749
```

## How It Works

### Customer Flow
1. Customer adds items to cart
2. Clicks "Checkout" → enters delivery address
3. Selects payment method (Stripe, Flutterwave, Paystack, or Bank Transfer)
4. Gets redirected to payment gateway (or gets bank details for bank transfer)
5. Completes payment
6. Redirected back to success page
7. Receives order confirmation email

### Admin (Your) Side
1. Go to Django admin: `/admin/gosh_main/order/`
2. View all orders with their payment status
3. See transaction IDs and payment details
4. Mark orders as processed/shipped

## File Structure

```
gosh_main/
  services/
    ├── payment_service.py          # Main payment router
    ├── stripe_gateway.py           # Stripe integration
    ├── paystack_gateway.py         # Paystack integration
    ├── flutterwave_gateway.py      # Flutterwave integration
    ├── webhooks.py                 # Webhook handlers
    └── email_service.py            # Email notifications

  views.py                           # Payment views
  models.py                          # Order & Payment models
  admin.py                           # Admin panel config
  urls.py                            # Payment URLs

  templates/
    ├── checkout_payment.html       # 4 payment options
    ├── checkout_success.html       # Success confirmation
    ├── checkout_bank_transfer.html # Bank transfer info
    └── payment_cancel.html         # Cancellation handling
```

## Webhook Setup (Production)

### Stripe Webhooks
In Stripe Dashboard → Developers → Webhooks:
```
URL: https://yourdomain.com/webhooks/stripe/
Events: checkout.session.completed, payment_intent.succeeded, payment_intent.payment_failed
```

### Paystack Webhooks
In Paystack Dashboard → Settings → Webhooks:
```
URL: https://yourdomain.com/webhooks/paystack/
```

### Flutterwave Webhooks
In Flutterwave Dashboard → Settings → Webhooks:
```
URL: https://yourdomain.com/webhooks/flutterwave/
```

## Production Checklist

- [ ] Switch API keys from `test_` to `live_` keys
- [ ] Update `SITE_URL` to your production domain
- [ ] Set up webhooks in all payment gateway dashboards
- [ ] Enable email confirmations
- [ ] Test full payment flow
- [ ] Set up payment notifications to admin
- [ ] Review order status workflow in admin

## Troubleshooting

### Payment Gateway Not Showing
- Check `.env` file has the correct API key
- Restart Django server: `python manage.py runserver`
- Check server logs for errors

### Webhook Not Working
- Verify webhook URL is publicly accessible
- Check webhook payload format matches gateway requirements
- Add logging to webhook handlers for debugging

### Email Not Sending
- For development: Check console output
- For production: Configure SMTP settings in `.env`

## Security Tips

1. **Never commit API keys to Git** - Use `.env` file only
2. **Use webhook signatures** to verify payment notifications
3. **Validate amounts** before sending to payment gateway
4. **HTTPS only** for production payment pages
5. **Sanitize user input** before storing payment info

## Support

Each payment gateway has test environments:
- **Stripe**: Always test first with `pk_test_` keys
- **Flutterwave**: Use `FLWPUBK_TEST` and `FLWSECK_TEST` prefixes
- **Paystack**: Use `pk_test_` and `sk_test_` keys

It's ready to go! 🚀
