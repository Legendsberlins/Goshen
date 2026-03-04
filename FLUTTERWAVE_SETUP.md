# Flutterwave Setup Instructions

## Step 1: Get Flutterwave API Keys
1. Go to https://dashboard.flutterwave.com
2. Sign up or log in to your account
3. Navigate to Settings → API Keys
4. Copy your Secret Key and Public Key

## Step 2: Add Environment Variables
Add these to your `.env` file:

```
FLUTTERWAVE_PUBLIC_KEY=pk_test_xxxxx  # or pk_live_xxxxx for production
FLUTTERWAVE_SECRET_KEY=sk_test_xxxxx  # or sk_live_xxxxx for production
```

## Step 3: Install Required Package
```bash
pip install requests
```

## Step 4: Payment Methods Supported
Flutterwave supports:
- ✓ Card payments (Visa, Mastercard, Verve)
- ✓ Bank transfers (Direct bank account)
- ✓ USSD (Nigerian mobile banking)
- ✓ Mobile money
- ✓ Google Pay
- ✓ Apple Pay

## Step 5: Webhook Setup (Optional but Recommended)
1. In Flutterwave dashboard, go to Settings → Webhooks
2. Set webhook URL to: `https://yoursite.com/webhooks/flutterwave/`
3. Enable webhook events for charge completion

## Step 6: Testing
Use these test card numbers:
- **Visa**: 5531886652142950, CVV: 564, Expires: 09/32
- **Mastercard**: 5399840000000000, CVV: 749, Expires: 09/32

Just follow these steps and the payment options will automatically appear!
