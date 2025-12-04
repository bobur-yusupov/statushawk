# System Architecture of project StatusHawk

This document contains system architecture of StatusHawk - Uptime Monitoring & Status Page. The core function is simple: a user registers, provides a URL, and platform continuously checks that URL's availability and response time, generating alerts and a public status page if it goes down. We build the application based on Microservices architecture for scalability.

## Introduction

### Project Ovewview

StatusHawk is an open-source, multi-tenant SaaS platform designed for uptime monitoring and incident communication. It allows users to register endpoints (HTTP/HTTPS, TCP, Ping) and continuously monitors their availability and response metrics. When downtime is detected, the system triggers multi-channel alerts and updates public-facing status pages.

Unlike simple cron-based scripts, StatusHawk is engineered as a distributed system capable of scaling to handle thousands of concurrent checks with high precision and minimal latency.

### Purpose and Scope

The primary objective of this architecture is to provide a robust framework that separates the management of monitors (CRUD) from the execution of monitors (Runners).

In Scope:

- Uptime Monitoring: Periodic HTTP, TCP and ICMP checks.
- Status Pages: Publicly accessible pages displaying historical uptime and active incidents.
- Alerting: Integration with Email.
- Team Management: Multi-user accounts with role-based access.

Out of Scope:

- Agent-based Monitoring: We do not install agents on user servers.
- Log Aggregation: We monitor availability, not internal application logs.

### Architectural Goals

Decisions in this document are driven by the following quality attributes:

- **Scalability**: The system must handle a growing number of monitors without degrading check accuracy. The Runner Service must be horizontally scalable to distribute the load of network requests.

- **Isolation**: A failure in the Web Dashboard or API must not stop the Runner Service from performing checks and sending alerts.

- **Data Integrity**: Historical uptime data is immutable and must be preserved accurately for SLA reporting.

- **Developer Experience**: As an open-source project, the system must be runnable locally via Docker Compose with minimal configuration, despite its distributed nature.
