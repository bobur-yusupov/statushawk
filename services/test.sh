#!/bin/bash

service=$1

docker compose -f docker-compose.test.yml run --rm $service sh -c "poetry run pytest ./app"
