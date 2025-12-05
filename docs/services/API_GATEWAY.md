# API Gateway & Core service - core service of StatusHawk

The main service of StatusHawk that manages User registration, management, billing and subscriptions. Also it is an entry point to all other services.

## Data models

For simplicity we use Django's default user model.

```plaintext
User:
- id (int)
- first_name
- last_name
- username
- email
- password
- is_active
```

We implement subscription and billing later.

## Authentication and Authorization

Django REST Framework has Token-based authorization by default. For simplicity we use this feature. The API Gateway is built together with auth service that enable authorization of incoming requests and redirect to other services.

### Endpoints

| Method | Endpoints | Description |
|--------|-----------|-------------|
| POST | `/api/auth/v1/signup` | Endpoint to register to StatusHawk |
| POST | `/api/auth/v1/login` | Login endpoint returns token after successful registration |
| POST |`/api/auth/v1/logout` | Logout endpoint to delete token from database |
| ALL METHODS |`/api/{service}/{endpoint}` | Proxy endpoint to redirect incoming request to a service |

### Standard response

All responses must follow to following standard

```json
{
    "status": "ok",
    "data": {
        "..."
    },
    "error": {
        "message": "..."
    },
    "timestamp": "..."
}
```

### Testing

For testing we use `pytest` library. All test file names should have `_test.py` postfix. We follow Test-driven development. To make the job easier each feature be documented along with edge cases.

### CI/CD

We use GitHub Actions to automate linting, testing and deployment.

### Docker Hub

I use my own Docker Hub account. Once a new commit be merged to `main` branch GitHub triggers pipeline to version, lint, type checking, test, build and pushing container to Docker Hub.

### Code quality check

We use `flake8` for linting, `mypy` for static code analysis and `black` to autoformat. Each function must have docstring

```python
def check_monitor(monitor_id: int) -> dict:
    """
    Executes a network check for the given monitor.

    Args:
        monitor_id (int): The primary key of the monitor to check.

    Returns:
        dict: A dictionary containing latency and status code.

    Raises:
        MonitorNotFoundError: If the ID does not exist.
    """
    pass
```
