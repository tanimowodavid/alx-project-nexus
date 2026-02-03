## Address Management

The **Address** module handles user-specific geographic data. It supports full **CRUD** (Create, Read, Update, Delete) functionality, allowing users to manage multiple shipping locations.

### Key Logic

- **Data Integrity:** Snapshot of addresses linked to existing orders are taken when an order is finalized so deleting an address does not affect historical transaction records.
- **Ownership:** Users can only access or modify addresses associated with their own accounts.

### API Endpoints

| Endpoint               | Method          | Description                                    |
| ---------------------- | --------------- | ---------------------------------------------- |
| `/api/addresses/`      | `GET`           | List all addresses for the authenticated user. |
| `/api/addresses/`      | `POST`          | Create a new address.                          |
| `/api/addresses/<id>/` | `GET`           | Retrieve details of a specific address.        |
| `/api/addresses/<id>/` | `PUT` / `PATCH` | Update an existing address.                    |
| `/api/addresses/<id>/` | `DELETE`        | Remove an address.                             |

---
