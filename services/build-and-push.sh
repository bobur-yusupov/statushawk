#!/bin/sh

# Set -e: Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
REGISTRY_USER="devyusupov" # Your Docker Hub username
SERVICE_DIR=$1
REPO_NAME="$REGISTRY_USER/statushawk/$SERVICE_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- 1. Validation Checks ---
if [ -z "$SERVICE_DIR" ]; then
    echo -e "${RED}Error: Please provide a service name (e.g., api-gateway).${NC}"
    exit 1
fi

echo -e "${BLUE}--- Starting build for service: $SERVICE_DIR ---${NC}"

# --- 2. Navigate and Get Version ---
if ! cd "$SERVICE_DIR"; then
    echo -e "${RED}Error: Directory $SERVICE_DIR not found.${NC}"
    exit 1
fi

# Get the SemVer tag (e.g., 1.0.1)
NEW_VERSION=$(poetry version --short)

# Define the full tags
VERSION_TAG="$REPO_NAME:$NEW_VERSION"
LATEST_TAG="$REPO_NAME:latest"

echo -e "${GREEN}Detected Version: v$NEW_VERSION${NC}"
echo -e "${BLUE}Building image with tags: $VERSION_TAG and $LATEST_TAG${NC}"

# --- 3. Build the Image and Tag ---
# Uses the current directory (.), applying both the version and latest tags
docker build -t "$VERSION_TAG" -t "$LATEST_TAG" .

echo -e "${GREEN}Image built successfully.${NC}"

# --- 4. Push to Docker Hub ---
# Assumes 'docker login' has been executed in the CI environment
echo -e "${BLUE}Pushing images to registry...${NC}"

docker push "$VERSION_TAG"
docker push "$LATEST_TAG"

echo -e "${GREEN}--- SUCCESS! Image pushed as v$NEW_VERSION and latest ---${NC}"

# Clean up build environment (optional, but good practice)
cd ..