# Quick Setup Guide - Payment Integration

## 1. Install Dependencies

```bash
pip install stripe requests
```

## 2. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 3. Set Environment Variables

### Option A: Using .env file (recommended)
Create a `.env` file in your project root:

```env
# Site Configuration
SITE_URL=http://localhost:8000

# Stripe (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_PUBLIC_KEY=pk_test_YOUR_KEY_HERE
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE

# Paystack (get from https://dashboard.paystack.com/#/settings/developers)
PAYSTACK_PUBLIC_KEY=pk_test_YOUR_KEY_HERE
PAYSTACK_SECRET_KEY=sk_test_YOUR_KEY_HERE
```

### Option B: Windows PowerShell
```powershell
$env:STRIPE_SECRET_KEY="sk_test_YOUR_KEY_HERE"
$env:PAYSTACK_SECRET_KEY="sk_test_YOUR_KEY_HERE"
$env:SITE_URL="http://localhost:8000"
```

## 4. Testing Locally

### Start the development server
```bash
python manage.py runserver
```

### Test the payment flow
1. Visit http://localhost:8000/shop/
2. Add items to cart
3. Go to checkout
4. Enter delivery address
5. Select payment method
6. For Stripe: Use test card `4242 4242 4242 4242`, any future expiry, any CVC
7. For Paystack: Use test card `5060666666666666666`, PIN: 123, OTP: 123456

## 5. Webhook Testing (Local Development)

For local webhook testing, use ngrok:

```bash
# Install ngrok from https://ngrok.com/
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Configure webhooks in gateway dashboards:
# Stripe: https://abc123.ngrok.io/webhooks/stripe/
# Paystack: https://abc123.ngrok.io/webhooks/paystack/
```

## 6. Admin Configuration

1. Create a superuser if you haven't:
```bash
python manage.py createsuperuser
```

2. Access admin at http://localhost:8000/admin/
3. View orders and payments under the "GOSH_MAIN" section

## Common Issues & Solutions

### "Payment gateway not found"
- Ensure environment variables are set correctly
- Restart the development server after setting environment variables

### "No module named stripe"
- Run: `pip install stripe`

### Webhooks not working locally
- Use ngrok to expose your local server
- Configure webhook URLs in gateway dashboards
- Check webhook signatures match in settings

### Order created but payment status "pending"
- Normal for bank transfer method
- For Stripe/Paystack: Check webhook configuration
- Verify payment in gateway dashboard

## Test Cards Reference

### Stripe
| Card Number | Result |
|------------|--------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 0002 | Declined |
| 4000 0000 0000 9995 | Insufficient funds |

### Paystack
| Card Number | PIN | OTP | Result |
|------------|-----|-----|--------|
| 5060666666666666666 | 123 | 123456 | Success |
| 5060000000000000006 | 123 | - | Declined |

## Next Steps

1. **Customize email templates** in `services/email_service.py`
2. **Adjust shipping costs** in `views.checkout_payment`
3. **Add more payment gateways** by extending `PaymentGateway` class
4. **Configure production settings** before deploying

## Production Deployment Checklist

- [ ] Switch to live API keys (remove `_test_`)
- [ ] Set `SITE_URL` to production domain
- [ ] Configure webhooks with production URLs
- [ ] Enable HTTPS/SSL
- [ ] Set `DEBUG=False` in settings
- [ ] Configure proper email backend (not console)
- [ ] Test with small real transactions
- [ ] Monitor webhook logs

## Getting API Keys

### Stripe
1. Sign up at https://stripe.com
2. Navigate to Developers → API keys
3. Copy "Publishable key" and "Secret key"
4. For webhooks: Developers → Webhooks → Add endpoint

### Paystack
1. Sign up at https://paystack.com
2. Navigate to Settings → API Keys & Webhooks
3. Copy "Public Key" and "Secret Key"
4. Add webhook URL in the webhooks section

## Support Resources

- **Stripe Docs**: https://stripe.com/docs
- **Paystack Docs**: https://paystack.com/docs
- **Full Documentation**: See `PAYMENT_INTEGRATION.md`
