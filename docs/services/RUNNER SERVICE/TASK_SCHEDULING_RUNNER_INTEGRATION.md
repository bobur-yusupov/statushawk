# Feature Design: Runner Service & Scheduler (Distributed Monolith)

|Metadata|Details|
|--------|-------|
|Status|Draft|
|Author|@bobur-yusupov|
|Created|2026-01-10"|
|Issue|#48|

## 1. Summary

Implement the **Runner Service** using a Distributed Monolith pattern. Instead of maintaining a separate codebase for the worker, we will reuse the API Gateway's Django/Python environment but deploy it as an isolated "Runner" service.
The Scheduling mechanism will use **Celery Recursive Tasks** (Self-Scheduling) rather than a central cron job or database polling loop, ensuring infinite scalability and isolation for each monitor.

## 2. Motivation

### 2.1 The Problem

- **Scalability:** A central scheduler that queries the database (`SELECT * FROM monitors WHERE next_check <= NOW()`) every second creates a massive database bottleneck as the number of monitors grows.
- **Blocking:** If the API Gateway performs HTTP checks directly (synchronously), slow websites will block user traffic and degrade dashboard performance.
- **Complexity:** Maintaining a separate Microservice (Go/Node) for the MVP phase adds unnecessary CI/CD pipelines, code duplication (DRY violation), and drift risks.

### 2.2 Goals

- **Reliable Scheduling**: Ensure monitors are checked exactly at their defined intervals (e.g., every 60s, 5m, 1h).
- **Decoupling**: The API Gateway should not perform the HTTP requests itself (blocking operations). It should only dispatch tasks.
- **Result Ingestion**: Process the results returned by the Runner (Success/Fail) and update the Monitor's status in the DB.

### 2.3 Out of Scope (Non-Goals)

- **Isolation:** The Runner must operate in its own Kubernetes Deployment. If the Runner crashes (e.g., OOM from too many threads), the API Gateway (Dashboard) must remain 100% available.
- **Precision:** Checks should occur at their specific intervals (e.g., exactly 60s after the last check finished).
- **Simplicity:** Use the existing Django Models (`Monitor`) without duplicating code across repositories.

## 3. Detailed Desgin

### 3.1. The "Distributed Monolith" Pattern

We use a single Docker image (`statushawk-backend`) but run it in two modes:

- **API Gateway:** Runs `gunicorn`. Handles HTTP traffic and user requests.
- **Runner Service:** Runs `celery worker`. Handles background monitoring tasks from the `runner_queue`.

### 3.2. The "Recursive Loop" Logic

Instead of a "Master Scheduler," every Monitor acts as a self-driving loop.

1. **Trigger**: User creates a Monitor -> API calls `check_monitor_task.delay(monitor_id)`.
2. **Execution**: Runner pops the task from Redis `runner_queue`.
    - **Validation

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

### 5.2 Testing Strategy

- **Unit Tests**: Test the DiscordFormatter class (does it produce valid JSON?).
- **Integration Tests**: Mock the requests.post call to ensure the pipeline triggers the sender.
- **Manual Verification**: Create a real Discord channel and spam it with test alerts.

## 6. Deployment / Rollout

- **Migrations**: Requires a DB migration for the new Enum value.
- **Feature Flag**: Is this behind a flag? `ENABLE_DISCORD_INTEGRATION = True`
