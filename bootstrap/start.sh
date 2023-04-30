#!/bin/sh

sleep 2
echo "Ishiki USB drive bootstrap starting"
python3 -u /opt/ishiki/bootstrap/bootstrap.py

if [ -f /opt/ishiki/bootstrap/resize_once.txt ]; then
    echo "resizing and rebooting"
    rm /opt/ishiki/bootstrap/resize_once.txt
    raspi-config --expand-rootfs
    reboot now
    exit 0
fi

if [ -f /media/usb/docker-compose.yaml ]; then
    echo "docker compose pull"
    cd /media/usb ; docker-compose stop
    cd /media/usb ; docker-compose pull
    echo "docker compose up"
    cd /media/usb ; docker-compose up --force-recreate -d
    docker system prune --force
fi

echo "monitoring usb"
python3 /opt/ishiki/bootstrap/monitor.py
exit 0