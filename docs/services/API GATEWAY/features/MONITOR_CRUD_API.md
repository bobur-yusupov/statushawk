# Monitor CRUD API

|Metadata|Details|
|--------|-------|
|Status|Approved|
|Author|@bobur-yusupov|
|Created|2026-01-10"|
|Issue|#31|

## 1. Summary

Implement the backend logic and API endpoints to allow authenticated users to Create, Read, Update, and Delete (CRUD) uptime monitors. This includes defining the database schema for a Monitor and validating user inputs (e.g., ensuring URLs are valid).

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- **Current state**: Users can sign up, but they cannot actually add websites to monitor.
- **Desired state**: A user can log in, click "Add Monitor", type `https://google.com`, set an interval (e.g., 5 mins), and save it.

### 2.2 Goals

- **Management**: Enable full lifecycle management of monitors.
- **Validation**: Prevent users from entering invalid data (e.g., htps://bad-url or negative intervals).
- **Ownership**: Ensure users can only modify their own monitors (Multi-tenancy isolation).

### 2.3 Out of Scope (Non-Goals)

- **Execution**: This feature only saves the configuration to the DB. The Runner Service (which actually pings the URL) is a separate task.
- **Alerting**: Configuring who gets emailed when this goes down is handled in the "Alerting" feature.

## 3. Detailed Desgin

### 3.1. Database changes

List new tables, columns, or indexes. Use your Schema Dictionary format.

- **Table**: monitors (Monitor model)
- **Column**: id (AutoField) -> PK, default -> Unique ID
- **Column**: user -> FK to User model -> Owner of the monitor
- **Column**: name (String, max 255) -> Friendly name (e.g. "Landing Page")
- **Column**: url (URLField, max 2048) -> The target to ping
- **Column**: type (Enum) -> HTTP (for MVP only HTTP)
- **Column**: status (Enum -> UP, DOWN, PAUSED) -> Current health state
- **Column**: interval (Integer, min 60, default 300) -> Frequency in seconds 300=5m
- **Column**: is_active (Boolean, default true) -> If False, runner ignores it
- **Column**: created_at (datetime, auto now add) -> audit trail

### 3.2. API Changes

Define the endpoints using the project's JSON standard.

**Base URL**: `/api/v1/monitors/`

1. **List monitors**: `GET /`
Returns all monitors belonging to the requesting user.

- Response

```json
{
    "count": 0,
    "next": "https://api.example.org/accounts/?page=5",
    "previous": "https://api.example.org/accounts/?page=3",
    "results": [
        "..."
    ]
}
```

2. **Create Monitor**: `POST /`

- Request:

```json
{
    "name": "Production API",
    "url": "https://api.myapp.com/health",
    "interval": 60,
    "type": "HTTP"
}
```

Validation logic:

- Check `url` starts with `http://` or `https://`
- Check `interval` >= 60 seconds (Prevent abuse).

3. **Retrieve Detail** `GET /{id}/`

Get details for a single monitor.

- **Security**: Must verify `monitor.user == request.user`. Returns `404` if ID exists but belongs to another user.

4. **Update Monitor** `PATCH /{id}/`

Update fields (e.g., change name or pause monitoring).

5. **Delete Monitor** `(DELETE /{id}/)`

Permanently remove the monitor and associated history.

- **Request**: `{"is_active": false}` (Pause the monitor)

### 3.4. Logic / Algorithms

Describe how the backend handles the logic.

- **Default Values**: If user sends no interval, default to 300 (5 minutes).
- **Status Field**: The user cannot `POST` a status like UP or DOWN. This field is Read-Only for the user; only the internal Runner service can update it.

## 4. Security Considerations

- SSRF Protection (Server-Side Request Forgery):
    - *Risk*: User adds a monitor for `http://localhost:5432` or `http://169.254.169.254` (AWS Metadata) to scan our internal network.
    - *Mitigation*: The Runner Service must implement a "Blocklist" for private IP ranges. (Note: Validating this at the API level is also good, but Runner validation ciritcal).
- Object Level Permissions:
    - Use DRF `IsAuthenticated`.
    - Ensure QuerySets are always filtered by `User`: `Monitor.objects.filter(user.request.user)`.

## 5. Edge cases and testing

### 5.1 Edge cases

- **Duplicate URLs**: Should we allow a user to monitor google.com twice? -> Yes, they might want different intervals.
- **Invalid URLs**: User enters htps://oops. -> Catch with Serializer validation.

### 5.2 Testing Strategy

- **Unit Tests**: 
    1. Test POST with valid data -> 201 Created.
    2. Test POST with interval 10 (too low) -> 400 Bad Request.
    3. Test GET sees only my monitors, not other users'.
    4. Test DELETE removes the record.

## 6. Deployment / Rollout

- **Migrations**: Run `poetry run python manage.py makemigrations` and `migrate` to create the table.
