# Plan
# - Connect to brickd
# - If we don't have brickd, quit
# - enumerate the devices and save contents to a file on the chosen volume
# - if the MQTT flag is set, also save initial tf-mqtt start up commands to a file on a volume

from tinkerforge.ip_connection import IPConnection # pylint: disable=import-error
from time import sleep
import logging

logging.basicConfig(level=logging.DEBUG)

tfIDs = []

def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version,
                device_identifier, enumeration_type):
    tfIDs.append([uid, device_identifier])

def enumerate():

    try:
        self.ipcon.connect(HOST, PORT)

        # Register Enumerate Callback
        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)

        # Trigger Enumerate
        self.ipcon.enumerate()
        sleep(1.5)
        return tfIDs

    except Exception as e:
        return []

def write_to_file(sensors):
    logging.info('Writing ')

if __name__ == "__main__":
    sensors = enumerate()
    write_to_file(sensors)