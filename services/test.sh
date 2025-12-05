#!/bin/bash

service=$1

docker compose run --rm $service sh -c "poetry run pytest ./app"
