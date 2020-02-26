import os
import shutil
import subprocess
import mount as mount_lib

WIFI_CONF_FILENAME = "wpa_supplicant.conf"
DST_FOLDER = "/etc/wpa_supplicant"


def look_for_wifi_conf():
    if check_usb(WIFI_CONF_FILENAME, DST_FOLDER):
        cmd = "sudo wpa_cli reconfigure"
        subprocess.call(cmd, shell=True)


def check_usb(search_name, dst_dir):
    devices = mount_lib.list_media_devices()
    found = []
    for device in devices:
        mount_lib.mount(device)
        if mount_lib.is_mounted(device):
            list_files(mount_lib.get_media_path(device), found, search_name)
            if len(found) > 0:
                filename = os.path.basename(found[0])
                dst_path = os.path.join(dst_dir, filename)
                if os.path.exists(dst_path):
                    os.remove(dst_path)
                if not os.path.exists(os.path.dirname(dst_path)):
                    os.makedirs(os.path.dirname(dst_path))
                shutil.copy(found[0], dst_path)
                mount_lib.unmount(device)
                return True
            else:
                mount_lib.unmount(device)
    return False


## recursivly look for file called search_name
def list_files(root, result, search_name):
    for filename in os.listdir(root):
        path = os.path.join(root, filename)

        if os.path.isfile(path):
            if filename == search_name:
                result.append(path)
                break

        elif os.path.isdir(path):
            list_files(path, result, search_name)


if __name__ == "__main__":
    look_for_wifi_conf()