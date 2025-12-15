# Setup Sentry and stdout logging to API Gateway service

|Metadata|Details|
|--------|-------|
|Status|In review|
|Author|@bobur-yusupov|
|Created|2025-12-15|
|Issue|#43|

## 1. Summary

Integrate **Sentry** (sentry.io) into the API Gateway for real-time error tracking and configure **Django Standard Logging** to output `INFO` logs to `stdout`. This hybrid approach ensures critical crashes trigger alerts (Sentry), while standard access/debug logs are preserved in a container-friendly format.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- **Current state**:
    1. **Errors**: When a 500 error occurs, evidence is buried in ephemeral pod logs.
    2. **Logs**: Django's default logging configuration often swallows `INFO` messages in production or writes them to files that vanish when pods restart.
- **Desired state**:
    1. **Errors**: Unhandled exceptions trigger immediate email alerts with stack traces.
    2. **Logs**: Every application event (login, request, background task) is streamed to `stdout` so Kubernetes can capture it.

### 2.2 Goals

- **Catch Unhandled Exceptions**: Automatically capture 500 Internal Server Errors via Sentry.
- **Contextual Debugging**: Capture User IDs and release tags associated with errors.
- **Standardize Output**: Configure Django to send all `INFO`, `WARNING`, and `ERROR` logs to Standard Output (stdout), making the app "Cloud Native" ready.

### 2.3 Out of Scope (Non-Goals)

- **Frontend Logging**: Strictly Backend (API Gateway).
- **Log Aggregation**: Sentry is for errors, not for storing general INFO logs (access logs). We will use Grafana Loki for that later.

## 3. Detailed Desgin

### 3.1. Developer Flow

Describe the UI changes or provide a link to a Figma/Screenshot.

- **Developer**: Pushes bad code that causes a `ZeroDivisionError`.
- **Sentry SDK**: Intercepts the crash before the process dies.
- **Sentry Dashboard**: Displays the error group, frequency, and exact line of code.
- **Email**: Alerts me.

### 3.2. Logic / Algorithms

Describe how the backend handles the logic.

- **Sampling**: To save quota, we will set `traces_sample_rate` to 0.1 (10%) for performance monitoring, but keep error reporting at 100%.
- **PII Filtering**: Sentry automatically scrubs credit cards. We must ensure we do not explicitly log raw passwords in variables sent to Sentry.

## 4. Security Considerations

- **DSN Secrecy**: The `SENTRY_DSN` acts as a key to write to our project. It must be stored in Kubernetes Secrets, not hardcoded in the repo.
- **Data Sanitization**:
    1. Ensure `Authorization` headers (Bearer tokens) are scrubbed. Sentry’s `DjangoIntegration` usually handles this default behavior well, but we must verify it.
    2. Ensure `send_default_pii=True` is compliant with our privacy policy (it sends User IDs/Emails so we can contact affected users).

## 5. Edge cases and testing

### 5.1 Edge cases

- **Sentry Downtime**: If [sentry.io](https://sentry.io) is down, the SDK is designed to fail silently (`network_timeout`). It will not crash the API Gateway.
- **Spamming Logs**: If a loop generates 1000 logs/sec, it increases K8s storage usage. We rely on the "INFO" level (not DEBUG) to keep volume manageable in production.

### 5.2 Testing Strategy

- **Verification (Sentry)**:
    1. Deploy to a Dev/Staging cluster.
    2. Run `python manage.py shell`
    3. Execute `raise Exception("This is a test error")`.
    4. Check Sentry Dashboard for the new issue.
- **Verification (Logs)**:
    1. Run the container.
    2. Execute `import logging; logging.info("Test Info Log")`.
    3. Run `kubectl logs <pod_name>` and confirm "Test Info Log" appears.

## 6. Deployment / Rollout

- **Helm Chart Updates**: Add Sentry variables to `values.yaml` (as defined previously). No specific variables needed for the `LOGGING` config as it uses standard `sys.stdout`.
