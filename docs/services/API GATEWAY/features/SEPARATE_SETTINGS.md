# Separate settings in API Gateway

|Metadata|Details|
|--------|-------|
|Status|Draft|
|Author|@bobur-yusupov|
|Created|2025-12-12"|
|Issue|#30|

## 1. Summary

Split monolith `settings.py` file into separate files is a standard best practice for Django projects. It allows you to keep production credentials secure and development tools (like debug toolbars) isolated.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- **Current state**: All project configuration settings are in one monolith `settings.py` file.
- **Desired state**: Configuration is split into modular files (`base.py`, `local.py`, `production.py`) to isolate environment-specific logic. improve security by keeping secrets out of version control, and ensure production settings are never accidentially applied in development.

### 2.2 Goals

- **Modular Configuration**: Separate settings into distinct files (`base.py`, `dev.py` and `production.py`) to handle shared, development-specific and production-specific configurations independently.
- **Security Enhancements**: Ensure production credentials and sensitive settings (like `DEBUG=False`) are strictly isolated from local development environments.
- **Environment Adaptability**: Enable seamless switching between environments (local dev vs. Kubernetes prod) simply by changing an environment variable (`DJANGO_SETTINGS_MODULE`).

### 2.3 Out of Scope (Non-Goals)

- We are not changing underlying infrastructure or deployment pipelines (e.g., Helm charts, CI/CD) in this task; we are only refactoring the Python code to read from them.
- We are not adding any new functional features or changing business logic; the application behavior should remain identical after the refactor.

## 3. Detailed Desgin

### 3.1. User Flow

Describe the UI changes or provide a link to a Figma/Screenshot.

- User navigates to Monitors > [Monitor Name] > Alerting.
- User sees a new section "Integrations".
- User selects "Discord" from a dropdown.
- Input field appears: "Webhook URL".
- User clicks "Save" (or "Test Integration").

### 3.2. File changes

List new tables, columns, or indexes. Use your Schema Dictionary format.

```plaintext
services/api-gateway/config/
├── __init__.py
├── asgi.py
├── wsgi.py
├── urls.py
└── settings/             # New folder
    ├── __init__.py       # Empty file (makes it a Python package)
    ├── base.py           # Shared settings (Apps, Middleware, Templates)
    ├── local.py          # Dev settings (Debug=True, Console Email)
    └── production.py     # Prod settings (Debug=False, S3, Security)
```

### 3.3. API Changes

Define the endpoints using the project's JSON standard.

**Endpoint**: `POST /api/v1/integrations/test/`

- Request

```json
{ 
    "type": "discord", 
    "url": "https://discord.com/api/webhooks/..." 
}
```

- Response

```json
{
    "status": "ok",
    "data": { "delivered": true }
}
```

### 3.4. Logic / Algorithms

Describe how the backend handles the logic.

- Runner Service: When an incident is created, the NotificationTask checks the AlertChannel type.
- Formatter: If type is DISCORD, format the message using Discord's specific JSON embed structure (color red for down, green for up).

## 4. Security Considerations

- **Validation**: How do we ensure the user doesn't paste a malicious URL (SSRF attack)?
    1. Mitigation: The backend must validate the URL host is actually
- **Permissions**: Can a "Read Only" member add a webhook? (No, must be Admin).
- **Encryption**: Is the Webhook URL sensitive? (Yes, treat it like a password).

## 5. Edge cases and testing

### 5.1 Edge cases

- **Rate Limiting**: What if Discord blocks our IP? (We should catch 429 errors and retry with exponential backoff).
- **Invalid URL**: What if the user deletes the webhook on Discord's side? (We should verify the webhook exists before saving).
- **Long Messages**: What if the error message is longer than Discord's 2000 char limit? (Truncate it).

### 5.2 Testing & strategy

- **Unit Tests**: Test the DiscordFormatter class (does it produce valid JSON?).
- **Integration Tests**: Mock the requests.post call to ensure the pipeline triggers the sender.
- **Manual Verification**: Create a real Discord channel and spam it with test alerts.

## 6. Deployment / Rollout

- **Migrations**: Requires a DB migration for the new Enum value.
- **Feature Flag**: Is this behind a flag? `ENABLE_DISCORD_INTEGRATION = True`
