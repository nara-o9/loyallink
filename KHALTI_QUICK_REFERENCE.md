# 🎯 Khalti Integration - Quick Reference Card

## 30-Second Activation

```bash
# 1. Get keys from https://dashboard.khalti.com/settings/keys

# 2. Set environment variables (PowerShell)
$env:KHALTI_PUBLIC_KEY="test_public_xxx"
$env:KHALTI_SECRET_KEY="test_secret_xxx"

# 3. Install dependencies
pip install requests

# 4. Run your app
python app.py

# 5. Test: Add product → Checkout → Select Khalti → Use test card
#    Card: 4111111111111111, CVV: 111, OTP: 111111
```

---

## Architecture at a Glance

```
Flask App
├── Config (app.py:19-21)
│   └── KHALTI_PUBLIC_KEY, KHALTI_SECRET_KEY
├── Routes
│   ├── /pay-with-khalti (POST) → Initiate payment
│   ├── /payment-success (GET) → Verify & Create order
│   └── /payment-failed (GET) → Handle failures
├── Templates
│   └── checkout.html → Payment method selection
└── Database
    ├── Order (new record created)
    ├── OrderItem (items in order)
    └── PointsTransaction (loyalty points)
```

---

## Key Code Snippets

### Configuration (app.py)
```python
app.config['KHALTI_PUBLIC_KEY'] = os.environ.get('KHALTI_PUBLIC_KEY', 'test_key')
app.config['KHALTI_SECRET_KEY'] = os.environ.get('KHALTI_SECRET_KEY', 'test_key')
```

### Initiate Payment (app.py:366-468)
```python
@app.route('/pay-with-khalti', methods=['POST'])
@login_required
def pay_with_khalti():
    # Validate cart & form
    # Calculate total
    # Store checkout_data in session
    # Call Khalti API
    # Redirect to payment_url
```

### Verify Payment (app.py:471-580)
```python
@app.route('/payment-success')
@login_required
def khalti_payment_success():
    # Get pidx from URL
    # Verify with Khalti API
    # Create Order in DB
    # Award loyalty points
    # Clear session
    # Show confirmation
```

### Checkout Form (checkout.html)
```html
<input type="radio" name="payment_method" value="khalti" onchange="updatePaymentUI()">
<script>
  if (paymentMethod === 'khalti') {
    form.action = '{{ url_for("pay_with_khalti") }}';
  }
</script>
```

---

## API Endpoints

### Khalti Initiate
```
POST https://a.khalti.com/api/v2/epayment/initiate/
Headers: Authorization: Key SECRET_KEY
Payload: {return_url, website_url, amount (in paisa), purchase_order_id, customer_info}
Response: {pidx, payment_url}
```

### Khalti Verify
```
POST https://a.khalti.com/api/v2/epayment/lookup/
Headers: Authorization: Key SECRET_KEY
Payload: {pidx}
Response: {pidx, status: "Completed"|"Pending"|"Failed", amount, transaction_id}
```

---

## Test Cards

| Card | Number | Expiry | CVV | OTP |
|------|--------|--------|-----|-----|
| Visa | 4111111111111111 | 12/25 | 111 | 111111 |

---

## Files Modified/Created

✅ **Modified:**
- `requirements.txt` - Added `requests`

✅ **Created:**
- `.env.example` - Environment template
- `KHALTI_INTEGRATION.md` - Full reference
- `KHALTI_SETUP_GUIDE.md` - Step-by-step guide
- `KHALTI_COMPONENTS.md` - Code details
- `KHALTI_FLOW_DIAGRAM.md` - Visual diagrams
- `KHALTI_SUMMARY.md` - Complete summary
- `KHALTI_QUICK_REFERENCE.md` - This file

---

## Environment Variables

```bash
# Development (Test Keys)
KHALTI_PUBLIC_KEY=test_public_key_xxxxxxxxxxxxxxxxxxxx
KHALTI_SECRET_KEY=test_secret_key_xxxxxxxxxxxxxxxxxxxx

# Production (Live Keys)
KHALTI_PUBLIC_KEY=live_public_key_xxxxxxxxxxxxxxxxxxxx
KHALTI_SECRET_KEY=live_secret_key_xxxxxxxxxxxxxxxxxxxx
```

---

## Payment Flow Summary

```
User fills checkout form
    ↓
Selects "Pay with Khalti"
    ↓
POST /pay-with-khalti
    ↓
App calculates total & calls Khalti API
    ↓
Khalti returns payment_url
    ↓
User redirected to Khalti payment page
    ↓
User enters card details
    ↓
Khalti processes payment
    ↓
Khalti redirects to /payment-success
    ↓
App verifies payment with Khalti API
    ↓
App creates Order in database
    ↓
App awards loyalty points
    ↓
User sees order confirmation
```

---

## Common Commands

```bash
# Install requests
pip install requests

# Set environment variables (PowerShell)
$env:KHALTI_PUBLIC_KEY="your_key"
$env:KHALTI_SECRET_KEY="your_key"

# Check environment variables
echo $env:KHALTI_PUBLIC_KEY

# Run app
python app.py

# Install from requirements
pip install -r requirements.txt
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| KeyError: 'KHALTI_SECRET_KEY' | Set environment variables before running app |
| Button doesn't redirect | Check form action is set correctly |
| Payment fails to verify | Ensure secret key is correct |
| Order not created | Check database connection and models |
| No loyalty points awarded | Verify user has loyalty_card record |

---

## Important URLs

- Khalti Dashboard: https://dashboard.khalti.com
- Test Payment: https://test-payment.khalti.com
- API Docs: https://docs.khalti.com/api
- Get Keys: https://dashboard.khalti.com/settings/keys

---

## Database Records After Payment

```
Order:
├── id (auto)
├── user_id
├── payment_method = 'khalti'
├── payment_status = 'completed'
├── total = amount
└── points_earned

OrderItem: (one per product)
├── order_id
├── product_id
├── quantity
└── subtotal

PointsTransaction:
├── user_id
├── points = earned_amount
├── type = 'earn'
└── description = 'Khalti Order #X'

Product:
└── stock -= quantity_ordered

LoyaltyCard:
└── points += earned_points
```

---

## Routes Summary

| Route | Method | Purpose | Auth |
|-------|--------|---------|------|
| /pay-with-khalti | POST | Initiate Khalti payment | ✅ |
| /payment-success | GET | Handle payment confirmation | ✅ |
| /payment-failed | GET | Handle payment failure | ✅ |
| /checkout | GET/POST | Checkout page | ✅ |
| /place_order | POST | Create order (COD) | ✅ |

---

## Security Checklist

- ✅ Secret key protected via environment variables
- ✅ User authentication required
- ✅ Server-side payment verification
- ✅ Cart validation
- ✅ Form validation
- ✅ Amount recalculation on server
- ⚠️ HTTPS in production (required for payment)
- ⚠️ Database backups (recommended)
- ⚠️ Payment logging (recommended)

---

## Success Indicators

After successful payment, you should see:
1. ✅ Order created in `Order` table
2. ✅ OrderItems in `OrderItem` table
3. ✅ Product stock decreased
4. ✅ Loyalty points increased
5. ✅ PointsTransaction created
6. ✅ Order confirmation page shown
7. ✅ Cart cleared from session
8. ✅ "Payment successful!" message

---

## Next Steps

1. **Get Khalti Keys** → https://dashboard.khalti.com/settings/keys
2. **Set Environment Variables** → `export KHALTI_PUBLIC_KEY=...`
3. **Test Integration** → Add product, checkout, select Khalti
4. **Verify Database** → Check Order, OrderItem, PointsTransaction created
5. **Go Live** → Switch to live keys in production

---

**You're ready to accept Khalti payments! 🎉**

For more details, see:
- `KHALTI_SETUP_GUIDE.md` - Complete setup guide
- `KHALTI_COMPONENTS.md` - Code reference
- `KHALTI_FLOW_DIAGRAM.md` - Visual diagrams
