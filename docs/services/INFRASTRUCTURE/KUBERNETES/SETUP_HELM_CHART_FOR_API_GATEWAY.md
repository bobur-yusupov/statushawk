# Setup Helm Chart for API Gateway

|Metadata|Details|
|--------|-------|
|Status|Implemented|
|Author|@bobur-yusupov|
|Created|2025-12-10"|
|Issue|#16|

## 1. Summary

Create a production-ready Helm Chart for the API Gateway service. This standardizes the deployment process, allowing developers to deploy the application to any Kubernetes cluster (Dev/Staging/Prod) using a single command with configurable parameters.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- Current state: Developers are not able to deploy API Gateway to K8s cluster.
- Desired state: A parameterized deployment package where configuration is separated from the manifest logic.

### 2.2 Goals

- **Templating**: Dynamic generation of Kubernetes manifests (Deployment, Service, Ingress, Job).
- **Configuration**: Control environment variables, resource limits, and replica counts via a simple `values.yaml` file.
- **Dependency Management**: Automatically handle dependencies like PostgreSQL and Redis if needed for local development.

### 2.3 Out of Scope (Non-Goals)

- **CI/CD Integration**: This task is only about creating the chart. The automation of `helm upgrade` in GitHub Actions is a separate ticket.
- **Secret Management**: We will use standard Kubernetes Secrets, not external vaults (like HashiCorp Vault) for this MVP.

## 3. Detailed Desgin

### 3.1. User Flow

Describe the UI changes or provide a link to a Figma/Screenshot.

1. **Build**: CI builds and pushes to Docker Hub through GitHub Actions (CI)
2. **Configure**: Developer edits `values.yaml` (changes `image.tag` to `v1.2.0`)
3. **Deploy**: Developer runs:

```bash
helm upgrade --install api-gateway ./charts/api-gateway -f values.prod.yaml
```

4. **Verify**: Helm waits for the Pods to become "Ready" before marking the release as successful.

### 3.2. Chart Structure

List new tables, columns, or indexes. Use your Schema Dictionary format.

```plaintext
charts/api-gateway/
├── Chart.yaml          # Metadata (name, version)
├── values.yaml         # Default configuration
├── templates/
│   ├── deployment.yaml # The main application logic
│   ├── service.yaml    # Internal networking (ClusterIP)
│   ├── ingress.yaml    # External access rules (Nginx)
│   ├── secret.yaml     # Sensitive env vars
│   └── _helpers.tpl    # Reusable template logic
```

### 3.3. Key Configuration (values.yaml)

Define the endpoints using the project's JSON standard.

```yaml
replicaCount: 2
image:
  repository: devyusupov/statushawk-api-gateway
  tag: "latest"
service:
  type: ClusterIP
  port: 8000
ingress:
  enabled: true
  hosts:
    - host: api-gateway.statushawk.internal
      paths: ["/"]
resources:
  limits:
    cpu: 500m
    memory: 512Mi
env:
  DEBUG: "False"
  DJANGO_SETTINGS_MODULE: "config.settings.production"
```

### 3.4. Logic / Algorithms

Describe how the backend handles the logic.

- **Migration Strategy**: The chart will include a Kubernetes InitContainer or a Pre-Install Hook Job to run `python manage.py migrate` before the new application pods start handling traffic.
- **Readiness Probes**: The Deployment template will configure a probe hitting `/api/health/` to ensure traffic is only sent to pods that are fully started.

## 4. Security Considerations

- **Secrets**: We must not commit actual passwords to `values.yaml`
    1. *Mitigation*: The `secret.yaml` template will reference values passed in via `--set` flags or from a secure `secrets.yaml` file that is git-ignored (or encrypted via SOPS).
- **Root Privileges**: The container should run as a non-root user.
    1. *Implementation*: Set securityContext.runAsUser: 1000 in the deployment template.
- **Network Policies**: By default, all traffic is allowed. We will restrict Ingress traffic to only come from the Ingress Controller.

## 5. Edge cases and testing

### 5.1 Edge cases

- **Database not ready**:If the API starts before the DB, it crashes.
    1. *Handling*: Use an `InitContainer` to wait for the DB, or rely on Kubernetes restarting the pod (CrashLoopBackOff) until the DB is up.
- **Bad Config**: If `ALLOWED_HOSTS` is missing, the app returns 400 errors.
    1. *Handling*: Validate required values in `_helpers.tpl` using the required function.

### 5.2 Testing & strategy

- **Linting**: Run `helm lint ./charts/api-gateway` in CI to catch syntax errors.
- **Dry Run**: Run `helm template ./charts/api-gateway` to verify the generated YAML looks correct without deploying it.
- **Minikube Test**: Deploy the chart to a local cluster and verify `kubectl get pods` shows status `Running`.

## 6. Deployment / Rollout

- **Versioning**: The `Chart.yaml` version will be bumped (e.g., `0.1.0` -> `0.1.1`) whenever the templates change.
- **Repo**: For now, the chart will live in the `/charts` directory of the monorepo. In the future, we can publish to a GitHub Pages Helm Repository.
