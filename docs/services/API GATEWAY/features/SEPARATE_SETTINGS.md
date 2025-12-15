# Separate settings in API Gateway

|Metadata|Details|
|--------|-------|
|Status|Implemented|
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

- N/A (Backend Refactor): This change is strictly internal. There are no UI changes or API endpoint changes.

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

### 3.4. Logic / Algorithms

Describe how the backend handles the logic.

1. **Base Settings** (`base.py`):
    - Contains `INSTALLED_APPS`, `MIDDLEWARE`, `TEMPLATES`, `REST_FRAMEWORK`.
    - Reads `SECRET_KEY` from env (with a fallback only for safety in CI).
2. **Entry Points**:
    - `manage.py`: Defaults to `config.settings.local` (developer convenience).
    - `wsgi.py`: Defaults to `config.settings.production` (production safety).
