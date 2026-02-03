# Cart Module

The **Cart App** manages the temporary storage of product variants for authenticated users. It serves as the bridge between the Product Catalog and the Order Checkout process.

## 🧠 Business Logic

- **Unique Constraints:** A user can only have one active `Cart`. Within that cart, a `ProductVariant` must be unique (quantities are incremented rather than creating duplicate rows).
- **Validation:** The cart prevents adding items that are:
- Marked as `is_active=False`.
- Exceed the current `stock_quantity`.

- **Performance:** Utilizes database-level aggregation (`Sum`, `F` expressions) to calculate totals, preventing N+1 query overhead.

## 🛠 API Reference

### Base URL: `/api/cart/`

| Endpoint        | Method   | Action        | Description                                                   |
| --------------- | -------- | ------------- | ------------------------------------------------------------- |
| `/`             | `GET`    | List/Detail   | Retrieves the authenticated user's cart and all items.        |
| `/`             | `POST`   | Create/Update | Adds an item via `variant_sku`. Increments if already exists. |
| `/reduce_item/` | `POST`   | Action        | Decreases quantity. Deletes item if quantity reaches 0.       |
| `/remove_item/` | `DELETE` | Action        | Completely removes a variant from the cart.                   |
| `/clear/`       | `DELETE` | Action        | Wipes all items from the cart.                                |

### Request Payload Example (Add Item)

```json
{
  "variant_sku": "TSHIRT-BLUE-L",
  "quantity": 2
}
```

## 🔒 Security

- **Authentication:** All endpoints require an `IsAuthenticated` permission.
- **Scope:** Users are strictly limited to their own cart via `get_queryset` filtering.

## 🚀 Future Improvements

- **Cart Expiry:** Implement a background task to clear carts older than 30 days.
- **Guest Carts:** Transition to session-based carts for unauthenticated visitors.
