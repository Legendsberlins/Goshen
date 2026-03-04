# How to Find Flutterwave API Keys

## Step-by-Step Guide to Get Your Flutterwave API Keys

### 1. Create/Login to Your Flutterwave Account
- Go to https://dashboard.flutterwave.com
- Sign up if you don't have an account
- Login with your email and password

### 2. Navigate to API Keys Section
**Method 1 (Most Direct):**
- Once logged in, click your **profile icon** (top right corner)
- Select **"Settings"** or look for **"API & Webhooks"** option
- You should see a page with your keys listed

**Method 2 (Alternative):**
- Look for the left sidebar menu
- Find **"Developer Settings"** or **"Integration"** section
- Click on **"API Keys"** or **"Credentials"**

### 3. Find Your Keys
You'll see two keys displayed:

**Public Key:**
- Looks like: `FLWPUBK_TEST-xxxxxxxxxxxxxxxxxxxxx` (for testing)
- Or: `FLWPUBK_LIVE-xxxxxxxxxxxxxxxxxxxxx` (for production)

**Secret Key:**
- Looks like: `FLWSECK_TEST-xxxxxxxxxxxxxxxxxxxxx` (for testing)
- Or: `FLWSECK_LIVE-xxxxxxxxxxxxxxxxxxxxx` (for production)

### 4. Copy and Store Securely
- Copy both keys
- Add them to your `.env` file like this:

```env
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST-xxxxx
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-xxxxx
```

- **Never** share these keys or commit them to Git!

## If You Still Can't Find Them:

1. **Check Your Account Status:**
   - Go to Settings → Account
   - Ensure your account is verified/activated
   - Some test accounts may have restricted access

2. **Email Flutterwave Support:**
   - Go to https://support.flutterwave.com
   - Request API key access if needed

3. **Alternative - Use Test Keys Directly:**
   - Flutterwave provides default test keys you can use:
   ```env
   FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST-37f4eb3f33ef
   FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-c1ba8d8c5b46c0e2f7bae3e9f2c5d6a8
   ```
   - These are publicly available test keys for learning

## Verify Your Keys Work

Test your connection after adding keys to `.env`:
1. Restart Django: `python manage.py runserver`
2. Add an item to cart
3. Go to checkout
4. Select "Flutterwave" payment option
5. If you see the payment form, your keys are working! ✓

---

**Still having issues?** The system has fallback payment methods (Stripe, Paystack, Bank Transfer) so you can skip Flutterwave and use those instead.
