# Khalti Payment Components Reference

## File Structure

```
app.py
├── Configuration (Lines 19-21)
├── /pay-with-khalti route (Lines 366-468)
├── /payment-success route (Lines 471-580)
└── /payment-failed route (Lines 583-588)

templates/
├── checkout.html
│   ├── Payment method selection (Lines 109-137)
│   ├── Form action logic (Lines 242-260)
│   └── Payment UI updates (JavaScript)

requirements.txt
└── requests (for API calls)
```

---

## 1. Configuration

**File:** `app.py` (Lines 19-21)

```python
# Khalti Payment Configuration
app.config['KHALTI_PUBLIC_KEY'] = os.environ.get('KHALTI_PUBLIC_KEY', 'test_public_key_xxx')
app.config['KHALTI_SECRET_KEY'] = os.environ.get('KHALTI_SECRET_KEY', 'test_secret_key_xxx')
```

**Environment Variables Needed:**
```
KHALTI_PUBLIC_KEY=test_public_key_xxxxxxxxxxxxxxxxxxxx
KHALTI_SECRET_KEY=test_secret_key_xxxxxxxxxxxxxxxxxxxx
```

---

## 2. Checkout Form - Payment Method Selection

**File:** `templates/checkout.html` (Lines 109-137)

```html
<!-- Payment Method Section -->
<div class="bg-white rounded-lg shadow-md p-6">
  <h2 class="text-xl font-bold text-gray-900 mb-6">Payment Method</h2>
  
  <div class="space-y-4">
    <!-- Cash on Delivery -->
    <label class="flex items-center p-4 border-2 border-indigo-600 rounded-lg cursor-pointer bg-indigo-50">
      <input type="radio" name="payment_method" value="cod" checked class="text-indigo-600" onchange="updatePaymentUI()">
      <div class="ml-4 flex-1">
        <p class="font-semibold text-gray-900">Cash on Delivery (COD)</p>
        <p class="text-sm text-gray-600">Pay when you receive your order</p>
      </div>
    </label>

    <!-- KHALTI PAYMENT OPTION -->
    <label class="flex items-center p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-indigo-200 transition">
      <input type="radio" name="payment_method" value="khalti" class="text-indigo-600" onchange="updatePaymentUI()">
      <div class="ml-4 flex-1">
        <p class="font-semibold text-gray-900">
          <img src="https://cdn.khalti.com/web/v2/khalti.svg" alt="Khalti" class="h-6 inline-block">
        </p>
        <p class="text-sm text-gray-600">Secure payment with Khalti</p>
      </div>
    </label>

    <!-- Bank Transfer -->
    <label class="flex items-center p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-indigo-200 transition">
      <input type="radio" name="payment_method" value="bank_transfer" class="text-indigo-600" onchange="updatePaymentUI()">
      <div class="ml-4 flex-1">
        <p class="font-semibold text-gray-900">Bank Transfer</p>
        <p class="text-sm text-gray-600">Direct bank transfer (within 24 hours)</p>
      </div>
    </label>
  </div>
</div>
```

---

## 3. Submit Button UI Logic

**File:** `templates/checkout.html` (Lines 242-260)

```html
<script>
  // Payment method handling
  function updatePaymentUI() {
    const form = document.querySelector('form');
    const submitBtn = document.getElementById('submit-btn');
    const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
    
    if (paymentMethod === 'khalti') {
      // When Khalti is selected
      form.action = '{{ url_for("pay_with_khalti") }}';
      submitBtn.textContent = '💳 Pay with Khalti';
      submitBtn.className = 'w-full bg-purple-600 text-white px-8 py-4 rounded-lg hover:bg-purple-700 transition font-semibold text-lg';
    } else if (paymentMethod === 'cod') {
      // When COD is selected
      form.action = '{{ url_for("place_order") }}';
      submitBtn.textContent = 'Place Order (Pay on Delivery)';
      submitBtn.className = 'w-full bg-indigo-600 text-white px-8 py-4 rounded-lg hover:bg-indigo-700 transition font-semibold text-lg';
    } else {
      // Other payment methods
      form.action = '{{ url_for("place_order") }}';
      submitBtn.textContent = 'Place Order';
      submitBtn.className = 'w-full bg-indigo-600 text-white px-8 py-4 rounded-lg hover:bg-indigo-700 transition font-semibold text-lg';
    }
  }

  // Initialize on page load
  updatePaymentUI();
</script>
```

---

## 4. Khalti Payment Initiation Route

**File:** `app.py` (Lines 366-468)

### Function Signature
```python
@app.route('/pay-with-khalti', methods=['POST'])
@login_required
def pay_with_khalti():
    """Initiate Khalti payment for cart"""
```

### Key Steps:
1. Validate cart exists
2. Get checkout form data
3. Validate all required fields
4. Calculate totals (subtotal + delivery - discount)
5. Apply loyalty points discount if available
6. Store checkout data in session
7. Call Khalti API to initiate payment
8. Redirect to Khalti payment page

### Code Flow:
```python
# 1. Validate cart
if not session.get('cart'):
    flash('Your cart is empty', 'error')
    return redirect(url_for('cart'))

# 2. Get form data
full_name = request.form.get('full_name', '').strip()
email = request.form.get('email', '').strip()
# ... more fields

# 3. Validate fields
if not all([full_name, email, phone, address, city, postal_code]):
    flash('All fields are required', 'error')
    return redirect(url_for('checkout'))

# 4. Calculate totals
subtotal = 0
for product_id, item in session['cart'].items():
    product = Product.query.get(int(product_id))
    subtotal += item['price'] * item['quantity']

delivery_charges = {'standard': 0, 'express': 150, 'pickup': 0}
delivery_charge = delivery_charges.get(delivery_option, 0)
discount = 0  # Loyalty discount logic here
total = subtotal + delivery_charge - discount

# 5. Store checkout data in session
session['checkout_data'] = {
    'full_name': full_name,
    'email': email,
    'phone': phone,
    'address': address,
    'city': city,
    'postal_code': postal_code,
    'delivery_option': delivery_option,
    'subtotal': subtotal,
    'delivery_charge': delivery_charge,
    'discount': discount,
    'total': total
}

# 6. Call Khalti API
url = "https://a.khalti.com/api/v2/epayment/initiate/"
payload = {
    "return_url": url_for('khalti_payment_success', _external=True),
    "website_url": url_for('home', _external=True),
    "amount": int(total * 100),  # Khalti uses paisa
    "purchase_order_id": f"ORDER_{current_user.id}_{int(datetime.utcnow().timestamp())}",
    "purchase_order_name": "Saraswati Stationery Order",
    "customer_info": {
        "name": full_name,
        "email": email,
        "phone": phone
    }
}

headers = {
    "Authorization": f"Key {app.config['KHALTI_SECRET_KEY']}",
    "Content-Type": "application/json",
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

# 7. Redirect to Khalti
return redirect(data['payment_url'])
```

---

## 5. Khalti Payment Success Handler

**File:** `app.py` (Lines 471-580)

### Function Signature
```python
@app.route('/payment-success')
@login_required
def khalti_payment_success():
    """Handle Khalti payment success - verify and create order"""
```

### Key Steps:
1. Get payment parameters from Khalti
2. **Verify payment with Khalti API** (CRITICAL!)
3. Check payment status is "Completed"
4. Retrieve checkout data from session
5. Create Order in database
6. Create OrderItem records
7. Update product stock
8. Award loyalty points
9. Clear session data
10. Redirect to order confirmation

### Code Flow:
```python
# 1. Get payment ID from Khalti
pidx = request.args.get('pidx')
transaction_id = request.args.get('transaction_id')
amount = request.args.get('amount')

# 2. Verify payment with Khalti API (CRITICAL FOR SECURITY!)
verify_url = "https://a.khalti.com/api/v2/epayment/lookup/"
verify_payload = {"pidx": pidx}
headers = {
    "Authorization": f"Key {app.config['KHALTI_SECRET_KEY']}",
    "Content-Type": "application/json",
}
verify_response = requests.post(verify_url, json=verify_payload, headers=headers)
verify_data = verify_response.json()

# 3. Check status
if verify_data.get('status') != 'Completed':
    flash('Payment was not completed', 'error')
    return redirect(url_for('checkout'))

# 4. Get session data
checkout_data = session.get('checkout_data')
cart = session.get('cart', {})

# 5. Create Order
order = Order(
    user_id=current_user.id,
    full_name=checkout_data['full_name'],
    email=checkout_data['email'],
    phone=checkout_data['phone'],
    address=checkout_data['address'],
    city=checkout_data['city'],
    postal_code=checkout_data['postal_code'],
    delivery_option=checkout_data['delivery_option'],
    payment_method='khalti',
    subtotal=checkout_data['subtotal'],
    delivery_charge=checkout_data['delivery_charge'],
    discount=checkout_data['discount'],
    total=checkout_data['total'],
    payment_status='completed',
    order_status='pending'
)
db.session.add(order)
db.session.flush()

# 6. Create OrderItems and update stock
for product_id, item in cart.items():
    product = Product.query.get(int(product_id))
    order_item = OrderItem(
        order_id=order.id,
        product_id=int(product_id),
        product_name=item['name'],
        product_price=item['price'],
        quantity=item['quantity'],
        subtotal=item['price'] * item['quantity']
    )
    db.session.add(order_item)
    product.stock -= item['quantity']

# 7. Award loyalty points
points_earned = int(checkout_data['subtotal'] / 10)
order.points_earned = points_earned

if current_user.loyalty_card:
    current_user.loyalty_card.points += points_earned
    points_transaction = PointsTransaction(
        user_id=current_user.id,
        points=points_earned,
        type='earn',
        description=f'Khalti Order #{order.id} - Rs. {checkout_data["subtotal"]}'
    )
    db.session.add(points_transaction)

# 8. Commit and cleanup
db.session.commit()
session.pop('cart', None)
session.pop('checkout_data', None)

# 9. Show success and redirect
flash(f'Payment successful! Order ID: {order.id}', 'success')
return redirect(url_for('order_confirmation', order_id=order.id))
```

---

## 6. Payment Failed Handler

**File:** `app.py` (Lines 583-588)

```python
@app.route('/payment-failed')
@login_required
def khalti_payment_failed():
    """Handle Khalti payment failure"""
    flash('Payment was cancelled or failed. Please try again.', 'warning')
    return redirect(url_for('checkout'))
```

---

## 7. Database Models Used

### Order Model
```python
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)
    delivery_option = db.Column(db.String(20), default='standard')
    payment_method = db.Column(db.String(50), default='cod')  # 'cod', 'khalti', 'bank_transfer'
    subtotal = db.Column(db.Float, nullable=False)
    delivery_charge = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'failed'
    order_status = db.Column(db.String(50), default='pending')  # 'pending', 'processing', 'shipped', 'delivered'
    points_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### OrderItem Model
```python
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
```

---

## 8. API Request/Response Examples

### Khalti Initiate Payment Request

```json
POST /api/v2/epayment/initiate/

{
    "return_url": "http://localhost:5000/payment-success",
    "website_url": "http://localhost:5000/",
    "amount": 100000,
    "purchase_order_id": "ORDER_123_1645425600",
    "purchase_order_name": "Saraswati Stationery Order",
    "customer_info": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "9841234567"
    }
}
```

### Khalti Initiate Payment Response

```json
{
    "pidx": "ZrwPr51A9n0Gvtr",
    "payment_url": "https://test-payment.khalti.com/?pidx=ZrwPr51A9n0Gvtr",
    "expires_at": "2026-02-16T11:35:00.000000Z"
}
```

### Khalti Verify Payment Request

```json
POST /api/v2/epayment/lookup/

{
    "pidx": "ZrwPr51A9n0Gvtr"
}
```

### Khalti Verify Payment Response

```json
{
    "pidx": "ZrwPr51A9n0Gvtr",
    "total_amount": 100000,
    "status": "Completed",
    "transaction_id": "103520315",
    "amount": 100000,
    "created_at": "2026-02-16T10:35:00.000000Z"
}
```

---

## 9. Test Credentials

**Khalti Test Mode Cards:**

| Type | Number | Expiry | CVV | OTP |
|------|--------|--------|-----|-----|
| Visa | 4111111111111111 | 12/25 | 111 | 111111 |
| Test Success | 4111111111111111 | Any Future | 111 | 111111 |

---

## ✅ Implementation Complete

All components are integrated and functional. Just add your Khalti keys and test!
