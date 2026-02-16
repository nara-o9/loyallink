# Khalti Payment Flow - Visual Diagram

## Complete Payment Flow Sequence

```
USER                    YOUR                KHALTI                  DATABASE
                        APP
│                       │                    │                       │
│ 1. Select Products    │                    │                       │
├──────────────────────►│                    │                       │
│                       │                    │                       │
│ 2. Go to Checkout     │                    │                       │
├──────────────────────►│                    │                       │
│                       │                    │                       │
│ 3. Fill Form Data     │                    │                       │
├──────────────────────►│                    │                       │
│                       │                    │                       │
│ 4. Select Khalti      │                    │                       │
│    Payment            │                    │                       │
├──────────────────────►│                    │                       │
│                       │                    │                       │
│ 5. Submit Form        │                    │                       │
├──────────POST───────► │                    │                       │
│ /checkout             │ 6. Validate       │                       │
│                       │    Form           │                       │
│                       │                    │                       │
│                       │ 7. Calculate     │                       │
│                       │    Total          │                       │
│                       │                    │                       │
│                       │ 8. Store Data    │                       │
│                       │    in Session    │                       │
│                       │                    │                       │
│                       │ 9. Call Khalti   │                       │
│                       │    API (Initiate)│                       │
│                       ├───────POST/json──►│ 10. Create         │
│                       │                    │     Payment         │
│                       │                    │     Session         │
│                       │◄──payment_url───┤ 11. Return          │
│                       │                    │     Payment URL     │
│ 12. Redirect to       │                    │                       │
│     Khalti Payment    │◄─────redirect─────┤                       │
├◄──────html────────────┤                    │                       │
│                       │                    │                       │
│ 13. Enter Card        │                    │                       │
│     Details          │                    │                       │
├─────────────────────►│                    │                       │
│                       │                    │ 14. Process Payment  │
│                       │                    │                       │
│ 15. Complete Payment/  │                    │                       │
│     Cancel            │                    │                       │
├─────────────────────►│                    │                       │
│                       │                    │ 16. Verify Success   │
│                       │                    │                       │
│                       │ 17. Redirect to   │                       │
│                       │     /payment-success                       │
│                       │◄─────redirect─────┤                       │
│ 18. Receive           │                    │                       │
│     Redirect          │                    │                       │
├◄──────html────────────┤                    │                       │
│                       │                    │                       │
│                       │ 19. Get pidx from  │                       │
│                       │     URL params     │                       │
│                       │                    │                       │
│                       │ 20. Verify Payment │                       │
│                       │     with Khalti    │                       │
│                       ├────POST (pidx)────►│ 21. Check Status      │
│                       │                    │                       │
│                       │◄──status:completed┤                       │
│                       │                    │                       │
│                       │ 22. Create Order   │                       │
│                       │     in DB          ├──────INSERT Order───►│
│                       │                    │                       │
│                       │ 23. Create Order   │                       │
│                       │     Items          ├──INSERT OrderItems──►│ 24. Save Records
│                       │                    │                       │
│                       │ 25. Update Stock   │                       │
│                       │     in DB          ├──UPDATE Products────►│
│                       │                    │                       │
│                       │ 26. Award Loyalty  │                       │
│                       │     Points         ├──UPDATE LoyaltyCard──►│
│                       │                    │                       │
│                       │ 27. Create Points  │                       │
│                       │     Transaction    ├─INSERT Transaction──►│
│                       │                    │                       │
│                       │ 28. Clear Session  │                       │
│                       │     Data           │                       │
│                       │                    │                       │
│ 29. Show Success &    │                    │                       │
│     Order Details     │←───show HTML───────┤                       │
│                       │                    │                       │
```

---

## State Transitions

### Happy Path ✅
```
Start
  │
  ├─► Cart Validated ✅
  │     │
  │     ├─► Form Data Validated ✅
  │     │     │
  │     │     ├─► Total Calculated ✅
  │     │     │     │
  │     │     │     ├─► Khalti API Called ✅
  │     │     │     │     │
  │     │     │     │     ├─► Payment Page Shown ✅
  │     │     │     │     │     │
  │     │     │     │     │     ├─► User Completes Payment ✅
  │     │     │     │     │     │     │
  │     │     │     │     │     │     ├─► Payment Verified ✅
  │     │     │     │     │     │     │     │
  │     │     │     │     │     │     │     ├─► Order Created ✅
  │     │     │     │     │     │     │     │     │
  │     │     │     │     │     │     │     │     ├─► Stock Updated ✅
  │     │     │     │     │     │     │     │     │     │
  │     │     │     │     │     │     │     │     │     ├─► Points Awarded ✅
  │     │     │     │     │     │     │     │     │     │     │
  │     │     │     │     │     │     │     │     │     │     └─► Success! ✅
```

### Error Paths ❌
```
Start
  │
  ├─► Empty Cart? ──► Redirect to Cart ❌
  │
  ├─► Missing Fields? ──► Show Error ❌
  │
  ├─► Stock Unavailable? ──► Show Error ❌
  │
  ├─► Khalti API Error? ──► Show Error ❌
  │
  ├─► User Cancels Payment? ──► Return to Checkout ❌
  │
  ├─► Payment Verification Failed? ──► Show Error ❌
  │
  └─► Database Error? ──► Show Error ❌
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CHECKOUT PAGE                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Form Fields:                                           │ │
│  │ - Full Name, Email, Phone                             │ │
│  │ - Address, City, Postal Code                          │ │
│  │ - Delivery Option (Standard/Express/Pickup)           │ │
│  │ - Payment Method (COD/Khalti/Bank Transfer)           │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ User selects Khalti
                       │ and submits form
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                /pay-with-khalti Route                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Validate Form Data                                  │ │
│  │ 2. Calculate Total:                                    │ │
│  │    - Get items from session['cart']                    │ │
│  │    - Calculate subtotal                                │ │
│  │    - Add delivery charges                              │ │
│  │    - Apply loyalty discount                            │ │
│  │ 3. Store in session['checkout_data']                   │ │
│  │ 4. Call Khalti API /epayment/initiate/                │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Send payment_url
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              KHALTI PAYMENT GATEWAY                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Khalti Payment Initiation API Response:               │ │
│  │ {                                                       │ │
│  │   "pidx": "payment_id_from_khalti",                   │ │
│  │   "payment_url": "https://khalti.com/pay?...",       │ │
│  │   "expires_at": "2026-02-16T11:35:00Z"                │ │
│  │ }                                                       │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ User enters card details
                       │ and completes payment
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│        KHALTI REDIRECTS WITH PAYMENT CONFIRMATION           │
│        /payment-success?pidx=xxxxx&transaction_id=xxxxx     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           /payment-success Route                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Extract pidx and amount from URL params             │ │
│  │ 2. Verify Payment with Khalti:                         │ │
│  │    POST /api/v2/epayment/lookup/ with pidx             │ │
│  │ 3. Check status == "Completed"                         │ │
│  │ 4. Retrieve session['checkout_data']                   │ │
│  │ 5. Create Order record:                                │ │
│  │    - user_id, full_name, email, phone                  │ │
│  │    - address, city, postal_code                        │ │
│  │    - delivery_option, payment_method                   │ │
│  │    - subtotal, delivery_charge, discount, total        │ │
│  │    - payment_status = 'completed'                      │ │
│  │    - order_status = 'pending'                          │ │
│  │ 6. Create OrderItem records for each product           │ │
│  │ 7. Update Product.stock for each item                  │ │
│  │ 8. Award Loyalty Points:                               │ │
│  │    - points_earned = subtotal / 10                     │ │
│  │    - Add to LoyaltyCard.points                         │ │
│  │    - Create PointsTransaction record                   │ │
│  │ 9. Commit to database                                  │ │
│  │ 10. Clear session['cart'] and session['checkout_data'] │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Show order confirmation
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  ORDER CONFIRMATION PAGE                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Display:                                               │ │
│  │ - Order ID                                             │ │
│  │ - Order Date & Time                                    │ │
│  │ - Order Items with prices                              │ │
│  │ - Total Amount                                         │ │
│  │ - Delivery Address                                     │ │
│  │ - Points Earned (for loyalty card)                     │ │
│  │ - Estimated Delivery Date                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Session & Database State Changes

### Before Payment
```
Session:
  - cart: {product_id: {name, price, quantity}, ...}

Database:
  - No Order record
  - No OrderItem records
  - User's loyalty points unchanged
  - Product stock unchanged
```

### During Payment
```
Session:
  - cart: {product_id: {name, price, quantity}, ...}
  - checkout_data: {full_name, email, phone, address, city, postal_code, delivery_option, subtotal, delivery_charge, discount, total}

Database:
  - Still no changes (awaiting verification)
```

### After Payment Success
```
Session:
  - cart: CLEARED
  - checkout_data: CLEARED

Database:
  - Order record CREATED with payment_status='completed'
  - OrderItem records CREATED for each product
  - Product stock DECREMENTED for each item
  - LoyaltyCard points INCREMENTED
  - PointsTransaction record CREATED
```

### Payment Failure
```
Session:
  - cart: UNCHANGED (ready to retry)
  - checkout_data: CLEARED

Database:
  - No changes
  - User can retry checkout
```

---

## Error Handling Flow

```
Checkout Form Submission
  │
  ├─ Cart Empty?
  │  └─► Flash 'Cart is empty' ❌
  │      Redirect to /cart
  │
  ├─ Missing Fields?
  │  └─► Flash 'All fields required' ❌
  │      Redirect to /checkout
  │
  ├─ Product Unavailable?
  │  └─► Flash 'Product not available' ❌
  │      Redirect to /cart
  │
  ├─ Khalti API Error?
  │  └─► Flash 'Failed to initiate payment' ❌
  │      Redirect to /checkout
  │
  ├─ Payment Cancelled?
  │  └─► Flash 'Payment cancelled' ⚠️
  │      Redirect to /checkout
  │
  ├─ Verification Failed?
  │  └─► Flash 'Payment verification failed' ❌
  │      Redirect to /checkout
  │
  └─ Success?
     └─► Flash 'Payment successful!' ✅
         Redirect to /order_confirmation
```

---

## Security Checkpoints

```
1. Authentication Check
   └─ @login_required decorator on all routes
      Only logged-in users can pay

2. Cart Validation
   └─ Verify cart items exist
      Verify products are available in stock

3. Form Validation
   └─ All required fields filled
      Phone number format validation

4. Amount Validation
   └─ Calculate amount server-side
      Compare with payment request

5. Payment Verification
   └─ Verify with Khalti API using SECRET KEY
      Check payment status == 'Completed'

6. Session Validation
   └─ Verify checkout_data exists in session
      Validate amount matches

7. Database Transaction
   └─ Use db.session.commit()
      Rollback on error
```

---

## Amount Calculation

```
Subtotal = Sum(product.price × quantity for each item)

Delivery Charges:
  - standard = 0
  - express = 150
  - pickup = 0

Discount:
  - If loyalty_card.points >= 100:
      draftable_points = min(100, loyalty_card.points)
      discount = draftable_points / 10
  - Else: discount = 0

Total = Subtotal + Delivery Charges - Discount

Khalti Amount = Total × 100  (converts to paisa)
```

---

## Test Flow

```
Login
  │
  ├─► Add Product to Cart
  │    │
  │    ├─ Quantity: 2
  │    └─ Product Price: Rs 500
  │
  ├─► View Checkout
  │    │
  │    ├─ Fill Form
  │    │  └─ Select "Khalti" Payment
  │    │
  │    └─ Click "💳 Pay with Khalti"
  │
  ├─► Khalti Payment Page
  │    │
  │    ├─ Card: 4111111111111111
  │    ├─ Expiry: 12/25
  │    ├─ CVV: 111
  │    └─ OTP: 111111
  │
  ├─► Payment Success
  │    │
  │    ├─► Order Created
  │    ├─► Stock Updated
  │    ├─► Loyalty Points Awarded
  │    └─► Confirmation Page Shown
  │
  └─► Order in My Orders
       └─ Status: Pending
          Payment: Completed
          Points Earned: 100
```

---

This comprehensive visual guide shows exactly how Khalti payment integration works in your application! 🎉
