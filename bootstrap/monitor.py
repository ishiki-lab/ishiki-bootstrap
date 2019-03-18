#!/usr/bin/env python3

import pyudev
import time
from bootstrap import start

def start():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')
    monitor.start()

    for device in iter(monitor.poll, None):
        time.sleep(4)
        start()

if __name__ == '__main__':
    start()