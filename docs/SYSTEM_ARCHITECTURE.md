# System Architecture of project StatusHawk

This document contains system architecture of StatusHawk - Uptime Monitoring & Status Page. The core function is simple: a user registers, provides a URL, and platform continuously checks that URL's availability and response time, generating alerts and a public status page if it goes down. We build the application based on Microservices architecture for scalability.

## Introduction

### Project Overview

A concise summary of **StatusHawk** as a multi-tenant SaaS application for uptime monitoring, status pages, and notification alerting.

### Business Goals

- Provide real-time monitoring of customer endpoints.
- Support a customizable, public-facing status page for each tenant.
- Achieve high availability and scalability for asynchronous monitoring jobs.

## Microservices

| Service Name | Primary Function | Technology Stack | Data Store |
|--------------|------------------|------------------|------------|
| Frontend     | User Interface (SPA) | React, Vite      | N/A        |
| API Gateway  | Auth & Routing | DRF | PostgreSQL |
| Account Service | User & Billing CRUD | DRF | PostgreSQL |
| Monitor Service | Config & Check Storage | DRF | PostgreSQL |
| Runner Service | Asynchronous Monitoring | Python / Celery | Redis (Broker/Cache), PostgreSQL (History) |

### Inter-Service Communication

- **Synchronous Communication**: All requests from the Frontend go through the API Gateway. The Gateway communicates with internal services using standard RESTful HTTP/JSON over Kubernetes' internal ClusterIP Services.
- **Asynchronous Communication**: The Monitor Service sends monitoring jobs to the Runner Service via a message queue (Redis). This ensures the API Gateway does not wait for long-running checks.
