#!/bin/bash

service=$1

docker compose -f docker-compose.test.yaml run --rm $service sh -c "poetry run pytest"
