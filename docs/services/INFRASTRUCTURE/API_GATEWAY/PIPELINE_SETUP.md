# GitHub Actions setup for API Gateway

|Metadata|Details|
|--------|-------|
|Status|Implemented|
|Author|@bobur-yusupov|
|Created|2025-12-08"|
|Issue|#7|

## 1. Summary

Create a comprehensive GitHub Actions CI/CD pipeline for the API Gateway service. This pipeline, defined in `.github/workflows/api-gateway-ci.yml`, will execute linting, run unit tests, automatically determine the semantic version, build the Docker image, and push it to Docker Hub.

## 2. Motivation

### 2.1 The Problem

Why are we doing this? What pain points does the user have?

- Current state: Development relies on manual testing, versioning, and deployment, which is error-prone and time-consuming.
- Desired state: An automated CI/CD pipeline to guarantee code quality, enforce semantic versioning, and streamline the deployment process.

### 2.2 Goals

- Automate unit testing using `pytest` and code quality checks (`flake8`) on every Push/Pull Request.
- Automate semantic versioning based on conventional commit prefixes (e.g., fix: for Patch and feat: for Minor). (Major.Minor.Path)
- Automate the building of the production-ready container image and push it to Docker Hub upon merge to the main branch.
- Increase developer velocity by removing manual build/push steps.

### 2.3 Out of Scope (Non-Goals)

- **Deployment to Kubernetes (CD)**: The pipeline will stop after pushing the image to Docker Hub. Actual deployment (Helm/ArgoCD rollout) will be handled by a separate process/system.
- **Integration Tests**: The pipeline will only run fast unit tests. Integration tests requiring a live database will be run separately or locally.

## 3. Detailed Desgin

### 3.1. Pipeline Structure and Triggers

The pipeline will be defined in `.github/workflows/api-gateway-ci.yml` and will run under two conditions:

- **Pull Request (PR)**: Triggered on `pull_request` to main. This run executes Linting and Testing only (no versioning or pushing).
- **Push to main**: Triggered on push to `main`. This executes all steps including Versioning, Building, and Pushing the image.

### 3.2. Job Breakdown (Sequential Steps)

The CI/CD process will use a single job with conditional steps:

|Step|Action/Tool|Trigger Condition|Rationale|
|----|-----------|-----------------|---------|
|1. Setup Python | `actions/setup-python` | Always | Speeds up dependency installation using cached poetry environments. |
|2. Install Dependencies | `poetry install` | Always | Installs dependencies specified in `poetry.lock`|
|3. Linting & Formatting | `flake8` | Always | Fails the build if code quality standards are not met. |
|4. Run tests | `pytest` | Always | Executes all unit tests (must pass for merge).|
|5.Versioning | `cycjimmy/semantic-release-action` | `if: github.ref == 'refs/heads/main'` | Determines the new SemVer tag (`0.0.1`, `0.1.0`) based on commit history since the last tag. |
|6. Build & Push | `docker/build-push-action` | `if: github.ref == 'refs/heads/main'` | Builds the container and pushes it to devyusupov/statushawk/api-gateway:latest and devyusupov/statushawk/api-gateway:vX.Y.Z |

### 3.3. Semantic Versioning Logic (Goals)

We will rely on a semantic release tool to parse the merged commit messages on the main branch:

- **PATCH Update (X.Y.Z+1)**: Triggered by commit message prefixes like `fix:`, `style:`, `refactor:`
- **MINOR Update (X.Y+1.0)**: Triggered by commit message prefixes like `feat:`, `feature:`
- **MAJOR Update (X+1.0.0)**: Triggered by commit message prefixes like `BREAKING CHANGE:`

## 4. Security Considerations

- **Secrets**: Docker Hub credentials (`DOCKER_USERNAME`, `DOCKER_PASSWORD`) will be stored exclusively as Encrypted Secrets in the GitHub repository settings. They will only be accessible to the Build/Push job.
- **Permissions**: The build job must use a `read:packages` token scope to retrieve dependencies and a `write:packages` scope to push images.

## 6. Deployment / Rollout

- **Artifacts**: The final artifact pushed to Docker Hub will have two tags: `latest` (for convenience) and the precise Semantic Version tag (`vX.Y.Z`).
- **Rollout**: The production environment (Kubernetes) will be configured to monitor the Docker Hub repository for new tags or use a GitOps tool to trigger deployment when the tag in the Helm chart is updated.
