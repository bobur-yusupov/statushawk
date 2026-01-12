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
    - **Validation**: Checks if Monitor is still `Active`. If Paused/Deleted, the loop stops.
    - **Action**: Pings the Target URL (HTTP GET)
    - **Persistence**: Saves `MonitorResult` to DB.
3. **Recursion**: The task schedules *itself* to run again in `N` seconds using `apply_async(countdown=monitor.interval)`.

### 3.3 Database Schema Changes

**Table: `monitors_monitorresult`** (New Table)

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Unique Result ID |
| `monitor_id` | UUID | FK | Link to parent Monitor |
| `status_code` | Int | NULL | HTTP Status (e.g., 200, 404, 500) |
| `response_time_ms` | Int | | Latency in milliseconds |
| `is_up` | Bool | | True if 2xx/3xx, False otherwise |
| `created_at` | DateTime | Index | Timestamp of check execution |

**Table: `monitors_monitor`** (Updates)

| Column | Type | Description |
| :--- | :--- | :--- |
| `last_checked_at` | DateTime | Timestamp of the last execution (for UI display) |
| `status` | Enum | UP / DOWN / PAUSED |

## 4. Technical Implementation

### 4.1 Queue Topology (Celery Routing)

We define strict routing in `settings.py` to prevent system tasks from blocking monitoring tasks.

- **`celery` (Default Queue):** System tasks (Emails, Reports, Cleanup). Low priority.
- **`runner_queue` (Dedicated Queue):** Monitor Checks only. High priority, high concurrency.

### 4.2 Code Logic (Pseudo-code)

```python
@shared_task(bind=True)
def check_monitor_task(self, monitor_id):
    # 1. Fetch & Validate
    try:
        monitor = Monitor.objects.get(id=monitor_id)
        if not monitor.is_active:
            return "Loop Stopped (Paused)"
    except Monitor.DoesNotExist:
        return "Loop Stopped (Deleted)"

    # 2. Execute Check
    start = time.time()
    try:
        response = requests.get(monitor.url, timeout=10)
        is_up = 200 <= response.status_code < 300
    except RequestException:
        is_up = False
    
    # 3. Save Result
    MonitorResult.objects.create(...)

    # 4. Schedule Next Run (Recursion)
    check_monitor_task.apply_async((monitor_id,), countdown=monitor.interval)
```
