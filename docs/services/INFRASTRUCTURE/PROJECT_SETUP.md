# Project Setup

|Metadata|Details|
|--------|-------|
| Status | Implemented |
|Author| @bobur-yusupov |
|Created| 2025-12-05 |
| Issue |#1|

## 1. Summary

Setup codebases for microservices, Docker containerization, initial Helm charts.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- Current state: No codebase for microservices and Helm to start project.
- Desired state: Create backend and frontend services along with Helm chart files.

### 2.2 Goals

- Setup Django projects
- Setup code quality check tools
- Setup frontend with React
- Dockerize each microservice
- Setup initial Helm charts

Code quality check tools: `mypy`, `black` and `flake8`

### 2.3 Out of Scope (Non-Goals)

- We are not setting up CI/CD and Container Repo. We are only focusing to setup initial codebase to enable developers start developing easily.
