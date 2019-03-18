#!/bin/sh

sleep 2
echo "bootstrap starting"
python3 -u /opt/ishiki/bootstrap/bootstrap.py

if [ -f /opt/ishiki/bootstrap/resize_once.txt ]; then
    echo "resizing and rebooting"
    rm /opt/ishiki/bootstrap/resize_once.txt
    raspi-config --expand-rootfs
    reboot now
    exit 0
fi

if [ -f /media/usb/docker-compose.yaml ]; then
    echo "docker compose up"
    docker-compose -f /media/usb/docker-compose.yaml pull
    docker-compose -f /media/usb/docker-compose.yaml up --force-recreate -d
fi

echo "monitoring usb"
python3 /opt/ishiki/bootstrap/monitor.py
exit 0