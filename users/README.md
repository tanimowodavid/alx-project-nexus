# User Management Module

The **User App** handles identity, authentication, and profile management. It uses **JWT (JSON Web Tokens)** for secure, stateless communication.

## 🧠 Key Features & Logic

### 1. Authentication Flow

The system utilizes `django-rest-framework-simplejwt`.

- **Registration:** Open to all users (`AllowAny`).
- **Logout:** Implements a security-first approach by **blacklisting** the refresh token, preventing further use of the session.

### 2. Profile Management

- **Dynamic Serializers:** The `UserProfileView` automatically switches between `UserSerializer` (for viewing) and `UserUpdateSerializer` (for modifying data) based on the HTTP method.
- **Security:** Users can only retrieve or modify their own profile data via `get_object` scoping.

### 3. Account Deletion (Soft Delete)

To maintain database integrity and historical records (like past orders), we do not perform hard deletions. Instead:

- **De-activation:** `is_active` is set to `False`.
- **Anonymization:** User identifiers (email/name) are scrambled or renamed to "Deleted User."
- **Session Termination:** The refresh token is blacklisted immediately upon account closure.

## 🛠 API Reference

| Endpoint                 | Method      | Action         | Description                                  |
| ------------------------ | ----------- | -------------- | -------------------------------------------- |
| `/auth/register/`        | `POST`      | Register       | Creates a new user account.                  |
| `/auth/profile/`         | `GET`       | View Profile   | Returns authenticated user details.          |
| `/auth/profile/`         | `PUT/PATCH` | Update Profile | Modifies user profile information.           |
| `/auth/change-password/` | `POST`      | Password       | Updates the user's password securely.        |
| `/auth/logout/`          | `POST`      | Logout         | Blacklists the provided refresh token.       |
| `/auth/delete-account/`  | `DELETE`    | Delete         | Anonymizes and deactivates the user account. |

## 🔒 Security Summary

- **Permissions:** All endpoints except Registration require a valid JWT.
- **Password Hashing:** Handled via Django's internal `set_password`, ensuring no plain-text storage.
- **Data Privacy:** Uses a custom `DeleteAccountView` logic to ensure user data is removed from active use while keeping the database records consistent.
