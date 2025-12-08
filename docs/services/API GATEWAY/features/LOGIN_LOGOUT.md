# User login and logout

|Metadata|Details|
|--------|-------|
|Status|Implemented|
|Author|@bobur-yusupov|
|Created|2025-12-08"|
|Issue|#5|

## 1. Summary

Add endpoint to login a user to authenticate with email and password. Add endpoint to logout the user.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- Current state: Currently we only have signup endpoint. Users can create an account, but cannot login.
- Desired state: Users be able to login and start or continue to use the platform. When not needed users can logout.

### 2.2 Goals

- Allow client-side to send request to backend through endpoint with provided data in body (email and password).
- Authenticate user with provided email and password.
- If successful return a generated token.
- If unsuccessful return an error message.
- Allow client-side to send `POST` request to backend through endpoint `/api/v1/accounts/logout` to logout the current user.
- Authorize the token
- Return successful logout message

### 2.3 Out of Scope (Non-Goals)

- **Password Reset**: "Forgot Password" functionality is handled in a separate issue.
- **Social Auth**: Login via Google, GitHub, or Facebook.
- **Multi-Factor Authentication (MFA)**: No 2FA will be implemented in this feature
- **Session Management**: We are using stateless Token authentication; we are not managing server-side sessions or cookies for this API.

## 3. Detailed Desgin

### 3.1. User Flow

Describe the UI changes or provide a link to a Figma/Screenshot.

- User visits to our website [https://statushawk.io](https://statushawk.io)
- Click on "Login" button on the main page.
- Fill the form (email and password).
- Submit form by clicking "Login" button.

```json
// Request
{
    "email": "user@example.com",
    "password": "SecurePassword!123"
}
```

- System authenticate the user
- After successful login receive token

```json
// Response
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### 3.2. Database changes

List new tables, columns, or indexes. Use your Schema Dictionary format.

We use `authtoken` module of `rest_framework` - a built in auth module. It comes with models, serializers, and views.

### 3.3. API Changes

Define the endpoints using the project's JSON standard.

**Endpoint**: `POST /api/v1/accounts/login`

- **Request body**

```json
{ 
    "email": "user@example.com",
    "password": "SecurePassword!123"
}
```

- **Success Response (200 OK)**

```json
{
    "status": "ok",
    "data": {
        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
    },
    "timestamp": "..."
}
```

- **Error Response (400 Bad Request / 401 Unauthorized)

```json
{
    "status": "error",
    "timestamp": "...",
    "error": {
        "message": "Unable to log in with provided credentials."
    }
}
```

**Endpoint**: `POST /api/v1/accounts/logout`

- Headers:
    1. `Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`
- Success Response (200 OK)

```json
{
    "status": "ok",
    "timestamp": "...",
    "data": {
        "message": "Successfully logged out.",
    }
}
```

### 3.4. Logic / Algorithms

Describe how the backend handles the logic.

#### Login Logic (LoginView)

1. **Validation**: The serializer validates that both `email` and `password` are present in the request.
2. **Authentication**: Use DRF's `ObtainAuthToken` view `rest_framework.authtoken.views.ObtainAuthToken`. Create a serializer for validation. Use `authenticate` function of Django to authenticate with email and password.
3. **Token Generation**:
    - If authentication succeeds: Get or create a token for the user using `Token.objects.get_or_create(user=user).
    - If authentication fails: Return a validation error.
4. **Response**: Serialize the token and return it in the standard JSON Structure

#### Logout Logic (LogoutView)

1. **Authentication**: Ensure the request has a valid token in the header (handled by `IsAuthenticated` permission class)
2. **Token Delection**: Access the token associated with the request user.
3. **Cleanup**: This effectively "logs out" the user by rendering that specific token invalid for future requests.

## 4. Security Considerations

- **Throttling**: Implement throttle on the login endpoint to prevent brute-force password guessing (e.g., limit to 5 attempts per minute per IP).

## 5. Edge cases and testing

### 5.1 Edge cases

- **Inactive User**: User tries to login but their account is disabled (`is_active=False`). The system should return a 401 error.
- **Missing Fields**: Request body is empty or missing password. Return 400 Bad Request.
- **Already Logged In**: If a user logs in again while having a valid token, the system returns the existing token (idempotent) or rotates the token (depending on security preference). For this iteration, we return the existing token.
- **Invalid Token on Logout**: User tries to logout with a fake or expired token. Return 401 Unauthorized.
- **Whitespace Handling**: Trailing spaces in email (e.g., `"user@example.com "`) should be trimmed or rejected.
- **Case Sensitivity**: Users entering `User@Example.com` should match `user@example.com` (depending on backend normalization logic).

### 5.2 Testing & strategy

#### Unit Tests

##### Login unit tests

1. `test_login_success`: Valid email and password returns 200 and a valid token string.
2. `test_login_failure_wrong_password`: Valid email but incorrect password returns 401.
3. `test_login_failure_nonexistent_user`: Email that does not exist in the DB returns 400 or 401 (generic error message to prevent enumeration).
4. `test_login_missing_fields`: Omission of email or password keys returns 400 Bad Request.
5. `test_login_invalid_email_format`: Sending "user" instead of `"user@example.com"` returns 400.
6. `test_login_inactive_user`: User with is_active=False returns 401.
7. `test_login_empty_strings`: Sending empty strings "" for credentials returns 400.
8. `test_login_throttling`: Attempting to login 10 times in 1 minute triggers a 429 Too Many Requests response.

##### Logout unit tests

1. `test_logout_success`: Request with valid Authorization header returns 200, and the token is deleted from the authtoken_token table.
2. `test_logout_unauthorized_no_token`: Request without headers returns 401.
3. `test_logout_invalid_token`: Request with a malformed or non-existent token returns 401.
4. `test_double_logout`: Calling logout twice with the same token. The first succeeds (200); the second fails (401) because the token was destroyed in step 1.

## 6. Deployment / Rollout
