#!/usr/bin/env bash

git pull
docker-compose -f app-compose.yaml stop
docker-compose -f app-compose.yaml build
docker-compose -f app-compose.yaml up -d
docker-compose -f app-compose.yaml logs --tail=100 -f