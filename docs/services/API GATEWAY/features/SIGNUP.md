# User Sign up

|Metadata|Details|
|--------|-------|
|Status| Draft |
|Author|@bobur-yusupov|
|Created|2025-12-05"|
|Issue|#3|

## 1. Summary

Add endpoint to register new user.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- Current state: Currently API Gateway does not have user registration endpoint.
- Desired state: Users be able to create a new account and start using the platform.

### 2.2 Goals

- Allow client-side to send request to backend through endpoint with provided data in body.
- Save user data (username, email, first name, last name and hashed password) to database.

### 2.3 Out of Scope (Non-Goals)

- We are not creating login endpoint. We do not implement user email verification.

## 3. Detailed Desgin

### 3.1. User Flow

Describe the UI changes or provide a link to a Figma/Screenshot.

- User visits to our website [https://statushawk.io](https://statushawk.io)
- Click on "Sign up" button on the main page.
- Fill the form and click "Sign up" button in the form
- After successful sign up redirect to dashboard [https://dashboard.statushawk.io](https://dashboard.statushawk.io)

### 3.2. Database changes

List new tables, columns, or indexes. Use your Schema Dictionary format.

- **Table**: User (inherited built-in AbstractUser model)
- **Column**: first_name (CharField)
- **Column**: last_name (CharField)
- **Column**: email (EmailField)

Abstract user model has username and password fields.

### 3.3. API Changes

Define the endpoints using the project's JSON standard.

**Endpoint**: `POST /api/v1/auth/signup`

- Request

```json
{ 
    "first_name": "User first name",
    "last_name": "User last name",
    "email": "user@example.com",
    "password": "securePassword!123"
}
```

- Response

```json
{
    "status": "ok",
    "data": {
        "id": "1",
        "first_name": "User first name",
        "last_name": "User last name",
        "email": "user@example.com",
    },
    "timestamp": "..."
}
```

### 3.4. Logic / Algorithms

Describe how the backend handles the logic.

1. Validation (Serializer):
    - Check `email` format.
    - Check `password` complexity (Min 8 chars, mixed case recommended).
    - Sanitize `first_name` / `last_name` (Strip HTML tags to prevent Stored XSS).
2. Uniqueness Check:
   - We use `unique=True` flag of Django ORM
   - If exists we raise `ValidationError`
3. Creation:
   - Call `User.objects.create_user(...)`
   - Important: This method automatically handles Password Hashing (PBKDF2) and salt generation. Never save raw password.
4. Serialization:
   - Convert new User object to JSON (Excluding the password field!)
   - Return HTTP 201

## 4. Security Considerations

- **Password Storage**: We rely on Django's default hasher (`PBKDF2` with `SHA256`). We must ensure we do not log the raw password in any server logs (Debug logs).
- **Rate Limiting (Throttling)**: To prevent bot attacks (creating 10k fake accounts), we must limit this endpoint.
   1. Limit: 5 requests per minute per IP Address
- **Input Sanitization**: While DRF handles SQL injection protection via ORM, we must ensure names aren't used for XSS payloads on the dashboard.
- **Enumiration Attacks**: Standard response for "Email already exists" reveals if a user is registered.

## 5. Edge cases and testing

### 5.1 Edge cases

- **Email Case Sensitivity**: `User@example.com` and `user@example.com` shoould be treated as the same user. Logic must normalize email to lowercase before saving/checking.
- **Unicode Characters**: Users signing up with names containing Emojis or Kanji, (Database encoding must be `UTF-8`).
- **Whitespace**: Users accidentally copying spaces `" user@example.com "`. Logic must `.strip()` inputs.
- **Database Downtime**: If DB is offline, return 503 Service Unavailable, not 500 with a stack trace.

### 5.2 Testing strategy

#### Unit Tests

##### User model test

- `test_create_user_success`
- `test_create_user_duplicate_email`
- `test_create_user_duplicate_username`
- `test_user_string`
- `test_email_normalization`
- `test_create_user_with_short_password`
- `test_user_defaults`
- `test_email_case_insensitivity_db`

##### User signup endpoint

- `test_signup_success`
- `test_signup_duplicate_email`
- `test_signup_short_password`
- `test_signup_email_normalization`
- `test_signup_method_not_allowed`
- `test_signup_unsupported_media_type`
- `test_signup_rate_limiting`

## 6. Deployment / Rollout
