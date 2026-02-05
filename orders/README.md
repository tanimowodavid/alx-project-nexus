# Orders Module

The **Orders** module handles checkout, payment integration, order lifecycle, and background processing for order confirmation and stock management.

## 🧾 Key Features & Logic

### 1. Order Snapshotting

- **Immutable snapshots:** Orders store snapshots of shipping details and product/variant information at purchase time (`shipping_address_snapshot`, `product_snapshot`, `variant_snapshot`) so historical orders remain accurate even after catalog changes.
- **Status flow:** Orders progress through `pending -> confirmed -> shipped -> delivered` with additional terminal states like `cancelled` and `refunded`.

### 2. Payment Integration (Paystack)

- **PaystackService:** Payments are initialized and verified via a dedicated `PaystackService` wrapper around Paystack's API.
- **Amount handling:** Paystack expects amounts in kobo/penny units, so amounts are multiplied by 100 before sending.
- **Tx reference:** Each order has a `tx_ref` used as the Paystack `reference` and callback identifier.
- **Callback flow:** After initialization Paystack redirects to the configured callback (example: `/orders/verify-payment/<tx_ref>`), where verification is performed and the order is queued for processing.
- **Config:** The Paystack secret key is read from `PAYSTACK_SECRET_KEY` in environment or Django settings.

### 3. Background Workers & Order Processing

- **Celery tasks:** Order finalization is handled by a Celery task (`process_order_payment`) which runs asynchronously to avoid blocking web requests.
- **Transaction safety:** The task wraps critical operations in `transaction.atomic()` and uses `select_for_update()` to lock the `Order` and `ProductVariant` rows.
- **Idempotency:** The task checks if the order is already `confirmed` to avoid double-processing if callbacks or retries happen.
- **Deadlock avoidance:** Variant IDs are sorted before locking to keep a consistent lock acquisition order across workers.
- **Stock deduction:** The task validates stock for each `OrderItem`, cancels the order if any variant is insufficient, or deducts stock and confirms the order when successful.
- **Cart cleanup & notifications:** On success the user's cart is cleared, totals reset, and email notifications are sent; on failure the user is notified of cancellation.

### 4. Resilience & Logging

- **Error handling:** Task exceptions are logged and return readable messages for observability.
- **Retries:** Celery retry strategies (if configured) can re-attempt transient failures; idempotency checks prevent duplicate side effects.

## 🛠 API Reference

| Endpoint                           | Method | Permission | Description                                      |
| ---------------------------------- | ------ | ---------- | ------------------------------------------------ |
| `/orders/initialize-payment/`      | `POST` | Auth       | Initialize Paystack payment, returns payment URL |
| `/orders/verify-payment/<tx_ref>/` | `GET`  | Public     | Paystack callback/verification endpoint          |
| `/orders/<id>/`                    | `GET`  | Auth       | Retrieve order details for the owner             |

### Initialize Request Example

### Verify / Callback Behavior

- The callback handler verifies the `tx_ref` with Paystack using `PaystackService.verify_payment` and enqueues `process_order_payment` for post-payment processing.

## 🔒 Security & Operational Notes

- **Permissions:** Order creation and retrieval require authenticated users; verify endpoints may be public depending on provider callback patterns but validate signatures/refs.
- **Secrets:** Keep `PAYSTACK_SECRET_KEY` out of source control and only in secure environment variables.
- **Workers:** Ensure a running Celery worker and message broker (e.g., Redis/RabbitMQ) for background tasks; configure task timeouts and retry policies appropriately.
