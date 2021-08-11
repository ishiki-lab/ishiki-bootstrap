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
    docker-compose -f /media/usb/docker-compose.yaml stop
    docker-compose -f /media/usb/docker-compose.yaml pull
    echo "Ishiki /boot folder bootstrap: docker compose up"
    docker-compose -f /media/usb/docker-compose.yaml up --force-recreate -d
    docker system prune --force
fi

exit 0