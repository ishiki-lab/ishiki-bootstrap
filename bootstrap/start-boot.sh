#!/bin/sh

sleep 2
echo "Ishiki /boot folder bootstrap: starting"
python3 -u /opt/ishiki/bootstrap/bootstrap-boot.py

if [ -f /opt/ishiki/bootstrap/resize_once.txt ]; then
    echo "Ishiki /boot folder bootstrap: resizing and rebooting"
    rm /opt/ishiki/bootstrap/resize_once.txt
    raspi-config --expand-rootfs
    reboot now
    exit 0
fi

if [ -f /boot/docker-compose.yaml ]; then
    echo "Ishiki /boot folder bootstrap: docker compose pull"
    cd /boot ; docker-compose stop
    cd /boot ; docker-compose pull
    echo "Ishiki /boot folder bootstrap: docker compose up"
    cd /boot ; docker-compose up --force-recreate -d
    docker system prune --force
fi

exit 0