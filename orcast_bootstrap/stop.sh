#!/bin/sh

echo "ishiki stopping orcast"

if [ -f /etc/opt/orcast/docker-compose.yaml ]; then
    docker-compose -f /etc/opt/orcast/docker-compose.yaml down
fi