#!/bin/bash

# Exit immediately if any command fails
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

service_name=$1

# 1. Validation Checks
if [ -z "$service_name" ]; then
    echo -e "${RED}Please provide a service name${NC}"
    exit 1
fi

if [ -d "$service_name" ]; then
    echo -e "${RED}Directory ./$service_name already exists.${NC}"
    exit 1
fi

echo -e "${GREEN}Checking system requirements...${NC}"
which python3 > /dev/null || { echo -e "${RED}Python3 not found.${NC}"; exit 1; }
which docker > /dev/null || { echo -e "${RED}Docker not found.${NC}"; exit 1; }

# 2. Create Directory
mkdir "$service_name"
cd "$service_name"

# 3. Setup Python Venv
echo -e "${GREEN}Creating Virtual Environment (.venv)...${NC}"
python3 -m venv .venv

# 4. Activate Venv (Only applies to this script's execution context)
source .venv/bin/activate

# 5. Install Poetry INSIDE the .venv
echo -e "${BLUE}Installing Poetry into local .venv...${NC}"
pip install --upgrade pip
pip install poetry

# 6. Initialize Project
echo -e "${GREEN}Initializing Poetry Project...${NC}"
# We typically want to disable creating a NEW venv, since we are already inside one
poetry config virtualenvs.create false --local

poetry init --name "$service_name" --description "Django Service" --python "^3.12" --no-interaction

# 7. Install Django & Tools
echo -e "${GREEN}Installing Dependencies...${NC}"
poetry add django django-cors-headers djangorestframework psycopg2-binary
poetry add --group dev black flake8 mypy pytest drf-spectacular

# 8. Create Django Project
echo -e "${GREEN}Creating Django Project Structure...${NC}"
# We use 'poetry run' or the direct path to ensure we use the venv's django-admin
poetry run django-admin startproject config .

# 9. Docker Setup
echo -e "${GREEN}Setting up Docker files...${NC}"
touch Dockerfile.dev
touch Dockerfile
touch .dockerignore
touch .env

echo -e "------------------------------------------------"
echo -e "${GREEN}Success! Project '$service_name' created.${NC}"
echo -e "${YELLOW}IMPORTANT: The script execution has finished, so the venv is now deactivated.${NC}"
echo -e "To activate the venv and start working, run:"
echo -e "${BLUE}cd $service_name && source .venv/bin/activate${NC}"
echo -e "------------------------------------------------"
