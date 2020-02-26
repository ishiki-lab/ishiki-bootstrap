#!/bin/sh

echo "ishiki bootstrap starting"
echo "ishiki checking wifi"
python3 -u /opt/ishiki/bootstrap/check_wifi.py

# resize if the file is there
if [ -f /opt/ishiki/bootstrap/resize_once.txt ]; then
    echo "ishiki resizing and rebooting"
    rm /opt/ishiki/bootstrap/resize_once.txt
    raspi-config --expand-rootfs
    reboot now
    exit 0
fi

echo "ishiki starting orcast"

# get and run the latest orcast bootstrap
docker pull paulharter/orcast-bootstrap:armhf
docker run --privileged -v /etc:/etc/orcast/host/etc --rm paulharter/orcast-bootstrap:armhf run_bootstrap.py

# if there is an after_bootstrap.sh script then run it
if [ -f /etc/opt/orcast/after_bootstrap.sh ]; then
    /etc/opt/orcast/after_bootstrap.sh
    rm /etc/opt/orcast/after_bootstrap.sh
fi

# if there is an docker-compose.yaml script then run it
if [ -f /etc/opt/orcast/docker-compose.yaml ]; then
    echo "docker compose pull"
    docker-compose -f /etc/opt/orcast/docker-compose.yaml pull
    docker-compose -f /etc/opt/orcast/docker-compose.yaml up -d --force-recreate
    docker system prune --force
fi

exit 0