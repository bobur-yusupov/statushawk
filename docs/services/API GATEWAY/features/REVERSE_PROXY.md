# API Gateway Reverse Proxy

|Metadata|Details|
|--------|-------|
|Status|Approved|
|Author|@bobur-yusupov|
|Created|2025-12-11"|
|Issue|#29|

## 1. Summary

Implement a **Reverse Proxy** mechanism within the API Gateway to securely route read-requests to downstream services. Because we follow a **Database-per-Service** architecture, the API Gateway has no direct access to metric data (Check Results). It must act as a **Policy Enforcement Point (PEP)**, validating user permissions against its own database before forwarding requests to the **Runner Service** to retrieve data.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- **Architecture Constraints**: We use separate databases.
    1. **Gateway DB**: Stores Users, Monitors, Billing.
    2. **Runner DB**: Stores Check Results, Latency, Incidents.

- **The Gap**: The Frontend needs to show a "History Graph" for a monitor. The API Gateway cannot query the **Runner DB** directly. The Runner Service is on a private network and cannot be accessed by the Frontend directly.

### 2.2 Goals

- **Single Entry Point**: The Frontend only communicates with `api-gateway.statushawk.local`
- **Security**: The Gateway performs Authentication (Token) and Authorization (Resource Ownership) using its local data.
- **Abstraction**: The Runner Service API can change without breaking the public API contract, as the Gateway acts as an adapter/proxy.

### 2.3 Out of Scope (Non-Goals)

- **Write Proxying**: Configuration changes (Creating Monitors) are handled via Event Synchronization (Redis/Celery), not by proxying HTTP write requests. This feature is for Read-Only data access.

## 3. Detailed Desgin

### 3.1. Architecture Flow

Describe the UI changes or provide a link to a Figma/Screenshot.

- **Client** sends `GET /api/v1/monitors/101/checks/` (Auth: Token).
- **Gateway (DRF)** validates the Token and populates `request.user`.
- **Gateway** checks **Gateway DB**: "Does User X own Monitor 101?"
    1. *If no*: return `404 Not Found`
    2. *If yes*: Proceed
- **Gateway** constructs internal request to Runner Service:
    1. URL: `http://runner-service:8000/internal/checks/?target_id=101`
- **Runner** queries **Runner DB** (`CheckResult` table) and returns JSON.
- **Gateway** forwards the JSON response to the Client.

### 3.2. API Changes

Define the endpoints using the project's JSON standard.

**Endpoint**: `GET /api/v1/monitors/{monitor_id}/checks/`

- **Logic**: Fetches history for a specific monitor.
- **Permissions**: `IsAuthenticated` & `IsOwner`.
- **QueryParams**: Forwarded to runner (e.g., `?limit=50`, `?start_date=...`).

## 4. Security Considerations

- **Trust Boundary**: The connection between Gateway and Runner is trusted (Cluster Network). The Gateway strips the user's `Authorization` header and replaces it with its own trust (Network Policy or a Shared Internal API Key if needed in the future).
- **Validation**: The Gateway MUST validate `monitor_id` against its own database. It must never blindly proxy `?target_id=X` from the user input.
- **Timeout Protection**: External calls must have strict timeouts (e.g., 3s) to prevent the public API from hanging if the internal Runner Service database is locked or slow.

## 6. Deployment / Rollout

- **Environment Variables**
    1. `RUNNER_SERVICE_URL`: `http://runner-service` (K8s Service DNS).
- **Kubernetes Network Policy**
    1. Allow `Ingress` -> `API Gateway` (Port 8000).
    2. Allow `API Gateway` -> `Runner Service` (Port 8000).
    3. Deny `Ingress` -> `Runner Service` (Runner is private).
