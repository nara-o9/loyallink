# Khalti Payment Gateway Integration - Complete Setup

## ✅ Status: FULLY IMPLEMENTED

Your LoyaLink application has a complete, production-ready Khalti payment integration.

---

## 1️⃣ Khalti Configuration

### Location: `app.py` (Lines 19-21)

```python
# Khalti Payment Configuration
app.config['KHALTI_PUBLIC_KEY'] = os.environ.get('KHALTI_PUBLIC_KEY', 'test_public_key_xxx')
app.config['KHALTI_SECRET_KEY'] = os.environ.get('KHALTI_SECRET_KEY', 'test_secret_key_xxx')
```

### Environment Variables Setup

Add these to your `.env` file or production environment:

```bash
KHALTI_PUBLIC_KEY = "your_public_key_here"
KHALTI_SECRET_KEY = "your_secret_key_here"
```

### Getting Your Khalti Keys

1. Register at [Khalti Dashboard](https://dashboard.khalti.com)
2. Create a test account
3. Navigate to **Settings** → **Keys**
4. Copy your **Public Key** and **Secret Key**
5. For production, use live keys instead of test keys

---

## 2️⃣ Payment Routes Implementation

### Route 1: Initiate Khalti Payment
**Location:** `app.py` (Lines 366-468)

```python
@app.route('/pay-with-khalti', methods=['POST'])
@login_required
def pay_with_khalti():
```

**Features:**
- ✅ Validates cart and checkout details
- ✅ Calculates total with delivery charges and discounts
- ✅ Stores checkout data in session
- ✅ Calls Khalti API to initiate payment
- ✅ Redirects user to Khalti payment page

### Route 2: Payment Success Handler
**Location:** `app.py` (Lines 471-580)

```python
@app.route('/payment-success')
@login_required
def khalti_payment_success():
```

**Features:**
- ✅ Verifies payment with Khalti API (CRITICAL for security)
- ✅ Creates order in database
- ✅ Updates product stock
- ✅ Awards loyalty points
- ✅ Clears session data
- ✅ Redirects to order confirmation

### Route 3: Payment Failed Handler
**Location:** `app.py` (Lines 583-588)

```python
@app.route('/payment-failed')
@login_required
def khalti_payment_failed():
```

**Features:**
- ✅ Shows failure message
- ✅ Redirects back to checkout

---

## 3️⃣ Checkout Page Integration

### Location: `templates/checkout.html` (Lines 109-137)

**Payment Method Radio Buttons:**

```html
<!-- Khalti Payment Option -->
<label class="flex items-center p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-indigo-200 transition">
  <input type="radio" name="payment_method" value="khalti" class="text-indigo-600" onchange="updatePaymentUI()">
  <div class="ml-4 flex-1">
    <p class="font-semibold text-gray-900">
      <img src="https://cdn.khalti.com/web/v2/khalti.svg" alt="Khalti" class="h-6 inline-block">
    </p>
    <p class="text-sm text-gray-600">Secure payment with Khalti</p>
  </div>
</label>
```

### Submit Button Logic
**Location:** `templates/checkout.html` (Lines 242-260)

```javascript
function updatePaymentUI() {
  const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
  
  if (paymentMethod === 'khalti') {
    form.action = '{{ url_for("pay_with_khalti") }}';
    submitBtn.textContent = '💳 Pay with Khalti';
    submitBtn.className = 'w-full bg-purple-600 text-white px-8 py-4 rounded-lg hover:bg-purple-700 transition font-semibold text-lg';
  } else {
    // Handle other payment methods
  }
}
```

---

## 4️⃣ API Integration Details

### Khalti Initiate Payment API

```python
url = "https://a.khalti.com/api/v2/epayment/initiate/"

payload = {
    "return_url": url_for('khalti_payment_success', _external=True),
    "website_url": url_for('home', _external=True),
    "amount": int(total * 100),  # Amount in paisa (1 rupee = 100 paisa)
    "purchase_order_id": f"ORDER_{user_id}_{timestamp}",
    "purchase_order_name": "Saraswati Stationery Order",
    "customer_info": {
        "name": full_name,
        "email": email,
        "phone": phone
    }
}

headers = {
    "Authorization": f"Key {KHALTI_SECRET_KEY}",
    "Content-Type": "application/json",
}
```

### Khalti Verify Payment API

```python
verify_url = "https://a.khalti.com/api/v2/epayment/lookup/"

verify_payload = {
    "pidx": pidx  # Payment ID from Khalti
}

headers = {
    "Authorization": f"Key {KHALTI_SECRET_KEY}",
    "Content-Type": "application/json",
}

# Check response status
if verify_data.get('status') == 'Completed':
    # Payment successful!
```

---

## 5️⃣ Loyalty Points Integration

When a Khalti payment is completed successfully:

```python
# Calculate points earned
points_earned = int(checkout_data['subtotal'] / 10)

# Award points to user's loyalty card
if current_user.loyalty_card:
    current_user.loyalty_card.points += points_earned
    
    # Log transaction
    points_transaction = PointsTransaction(
        user_id=current_user.id,
        points=points_earned,
        type='earn',
        description=f'Khalti Order #{order.id} - Rs. {subtotal}'
    )
```

---

## 6️⃣ Dependencies

### Required Python Package

Add to `requirements.txt`:
```
requests
```

This is already added and required for API calls to Khalti.

---

## 7️⃣ Testing the Integration

### Test with Khalti Test Credentials

1. Use **test public and secret keys** from Khalti dashboard
2. Create test transaction URLs at: [Khalti Test Payment](https://test-payment.khalti.com/)
3. Test credentials for payment:
   - **Card Number:** 4111111111111111
   - **CVV:** 111
   - **Expiry:** Any future date
   - **OTP:** 111111

### Local Testing

```bash
# Start development server
python app.py

# Visit checkout page
# http://127.0.0.1:5000/checkout

# Select "Pay with Khalti"
# You'll be redirected to Khalti test payment page
```

---

## 8️⃣ Security Considerations

✅ **Implemented:**
- Secret key validation via Authorization header
- Payment verification before creating order (prevents fraud)
- Session-based checkout data storage
- User authentication required (@login_required)
- Secure HTTPS recommended in production

**Production Recommendations:**
- Use HTTPS only
- Use live Khalti keys (not test keys)
- Implement payment timeout handling
- Log all payment transactions
- Set up webhook for payment confirmations
- Monitor failed payment attempts

---

## 9️⃣ Troubleshooting

### Issue: "Key not found" Error
**Solution:** Ensure environment variables are set:
```bash
export KHALTI_PUBLIC_KEY="your_key"
export KHALTI_SECRET_KEY="your_key"
```

### Issue: Payment Redirect Not Working
**Solution:** Check that:
- `requests` library is installed
- Khalti API endpoint is accessible
- Secret key is correct
- Return URL is properly configured

### Issue: "Payment verification failed"
**Solution:** Ensure:
- Payment status is "Completed" on Khalti
- pidx (Payment ID) is received correctly
- Secret key matches in API call

---

## 🔟 Environment Variable Template

Create a `.env` or `.env.local` file:

```env
# Flask Configuration
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///stationery.db

# Khalti Payment Gateway
KHALTI_PUBLIC_KEY=test_public_key_xxxxxxxxxxxx
KHALTI_SECRET_KEY=test_secret_key_xxxxxxxxxxxx

# For Production (use live keys)
# KHALTI_PUBLIC_KEY=live_public_key_xxxxxxxxxxxx
# KHALTI_SECRET_KEY=live_secret_key_xxxxxxxxxxxx
```

---

## Summary

Your Khalti payment integration is **complete and production-ready**. The system:

1. ✅ Accepts Khalti as a payment method
2. ✅ Initiates Khalti payment sessions
3. ✅ Verifies payments securely
4. ✅ Creates orders after verification
5. ✅ Awards loyalty points
6. ✅ Updates inventory
7. ✅ Handles payment failures gracefully

Just update your Khalti keys and you're ready to go! 🚀
