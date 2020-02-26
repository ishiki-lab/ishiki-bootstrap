import subprocess
import time
import socket
import shutil
import json
import os
import pwd
import grp
from mount import *

MOUNT_DIR = "/media/usb"
USERNAME = "ishiki"
WPA_SUPPLICANT_FILE = "/etc/wpa_supplicant/wpa_supplicant.conf"

def start():
    print("Bootstrap: Starting")

    # mount the usb
    if mount_usb():
        print("Bootstrap: Found the ishiki USB")
        settings_file = os.path.join(MOUNT_DIR, "settings.json")

        with open(settings_file, "r") as f:
            settings = json.loads(f.read())

        # these functions should ideally be idempotent and check first before updating anything

        clear_old_wifi()

        # set wifi credentials
        ssid, psk = get_wifi_creds(settings)
        if ssid:
            if not already_has_creds(ssid, psk):
                print("Bootstrap: Adding SSID=%s and PASSWORD=%s to wpa_supplicant.conf" % (ssid, psk))
                add_wifi_creds(ssid, psk)
            else:
                print("Bootstrap: Wifi already configured for %s" % ssid)
        else:
            print("Bootstrap: No ssid given")

        # configure eth0 ip address
        interface = "eth0"
        address = settings.get("eth0_address")
        netmask = settings.get("eth0_netmask")
        router = settings.get("eth0_router")
        set_ip_address(interface, address=address, netmask=netmask, router=router)

        captive_portal = settings.get("captive_portal")

        if captive_portal:
            # configure ap address
            set_ap_dhcpdc_conf("uap0", address="192.168.1.1", netmask="24")
            address = None
            netmask = None
            router = None
        else:
            set_ap_dhcpdc_conf("uap0", address=None, netmask=None)
            address = settings.get("wlan0_address")
            netmask = settings.get("wlan0_netmask")
            router = settings.get("wlan0_router")

        interface = "wlan0"
        set_ip_address(interface, address=address, netmask=netmask, router=router)

        subprocess.call(['sudo', 'systemctl', 'daemon-reload'])
        subprocess.call(['sudo', 'systemctl', 'restart', 'dhcpcd.service'])

        # set hostname
        host_name = settings.get("host_name")
        if host_name:
            set_hostname(host_name)

        # set timezone
        time_zone = settings.get("time_zone")
        if time_zone:
            set_time_zone(time_zone)

        # set public/private keys
        public_key = settings.get("public_key")
        private_key = settings.get("private_key")
        if public_key and private_key:
            add_keys(public_key, private_key)

        # configure ssh tunnel
        tunnel_host = settings.get("tunnel_host")
        docker_tunnel_port = settings.get("docker_tunnel_port")
        admin_tunnel_port = settings.get("admin_tunnel_port")
        tunnel_user = settings.get("tunnel_user")

        if tunnel_host and docker_tunnel_port and admin_tunnel_port and tunnel_user:
            print("Bootstrap: Docker tunnel configured to %s on port %s" % (tunnel_host, docker_tunnel_port))
            configure_ssh_tunnel(tunnel_host, docker_tunnel_port, tunnel_user, "2375", "docker_tunnel")
            print("Bootstrap: SSH tunnel configured to %s on port %s" % (tunnel_host, admin_tunnel_port))
            configure_ssh_tunnel(tunnel_host, admin_tunnel_port, tunnel_user, "22", "admin_tunnel")
    else:
        print("Bootstrap: Failed to find the ishiki USB")


def _replace_template_text(text, name, value):
    return text.replace("{{ %s }}" % name, value)


def clear_old_wifi():
    shutil.copyfile("/etc/wpa_supplicant/wpa_supplicant.backup", "/etc/wpa_supplicant/wpa_supplicant.conf")


def configure_ssh_tunnel(tunnel_host, tunnel_port, tunnel_user, dst_port, service_name):

    cmd = "systemctl stop %s.service" % service_name
    subprocess.call(cmd, shell=True)

    with open("/opt/ishiki/bootstrap/tunnel.service.template", "r") as f:
        template_text = f.read()

    template_text = _replace_template_text(template_text, "tunnel_host", tunnel_host)
    template_text = _replace_template_text(template_text, "tunnel_port", tunnel_port)
    template_text = _replace_template_text(template_text, "dst_port", dst_port)
    conf_text = _replace_template_text(template_text, "tunnel_user", tunnel_user)

    conf_file_path = "/etc/systemd/system/%s.service" % service_name

    if os.path.exists(conf_file_path):
        os.remove(conf_file_path)

    with open(conf_file_path, "w") as f:
        f.write(conf_text)

    os.chmod(conf_file_path, 755)

    cmd = "systemctl daemon-reload"
    subprocess.call(cmd, shell=True)
    cmd = "systemctl start %s.service" % service_name
    subprocess.call(cmd, shell=True)
    cmd = "systemctl enable %s.service" % service_name
    subprocess.call(cmd, shell=True)


def set_time_zone(time_zone):

    dst = "/etc/localtime"
    src = "/usr/share/zoneinfo/%s" % time_zone
    if os.path.exists(dst):
        if os.path.islink(dst):
            target = os.readlink(dst)
            if target == src:
                print("Bootstrap: Time zone already set to %s" % time_zone)
                return
            else:
                os.remove(dst)
        else:
            os.remove(dst)
    print("Bootstrap: Setting time zone to %s" % time_zone)
    os.symlink(src, dst)


def ensure_content_matches(file_path, content, mode, uid, gid):

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing_content = f.read()
        if existing_content == content:
            print("Bootstrap: File alread exists %s" % file_path)
            return
        else:
            os.remove(file_path)

    print("Bootstrap: Updating file %s" % file_path)
    with open(file_path, "w") as f:
        f.write(content)

    os.chmod(file_path, mode)
    os.chown(file_path, uid, gid)


def add_keys(public_key, private_key):

    ssh_dir = "/home/%s/.ssh" % USERNAME
    public_file = os.path.join(ssh_dir, "id_rsa.pub")
    private_file = os.path.join(ssh_dir, "id_rsa")
    uid = pwd.getpwnam(USERNAME).pw_uid
    gid = grp.getgrnam(USERNAME).gr_gid

    # ensure the dir
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, mode=700)
        os.chown(ssh_dir, uid, gid)

    ensure_content_matches(public_file, public_key, 644, uid, gid)
    ensure_content_matches(private_file, private_key, 600, uid, gid)


def add_wifi_creds(ssid, psk):
    cmd = 'wpa_passphrase "%s" "%s" >> /etc/wpa_supplicant/wpa_supplicant.conf' % (ssid, psk)
    subprocess.call(cmd, shell=True)
    time.sleep(1)
    cmd = "sudo wpa_cli reconfigure"
    subprocess.call(cmd, shell=True)
    time.sleep(3)


def get_wifi_creds(creds):
    return creds.get("ssid"), creds.get("psk")


def already_has_creds(ssid, psk):
    if os.path.exists(WPA_SUPPLICANT_FILE):
        with open(WPA_SUPPLICANT_FILE, "r") as f:
            existing = f.read()
        return  ssid in existing and psk in existing
    else:
        return False


def set_hostname(new_hostname):
    current_hostname = socket.gethostname()
    if new_hostname != current_hostname:
        print("Bootstrap: Setting host name to %s" % new_hostname)
        cmd = "sed -i 's/%s/%s/g' /etc/hostname" % (current_hostname, new_hostname)
        subprocess.call(cmd, shell=True)
        cmd = "sed -i 's/%s/%s/g' /etc/hosts" % (current_hostname, new_hostname)
        subprocess.call(cmd, shell=True)
        cmd = "" \
              "" \
              "# %s" % new_hostname
        subprocess.call(cmd, shell=True)
    else:
        print("Bootstrap: Host name already set to %s" % new_hostname)


def _list_files(root, result):
    for filename in os.listdir(root):
        path = os.path.join(root, filename)

        if os.path.isfile(path):
            if filename.startswith("settings"):
                result.append(path)
                break

        elif os.path.isdir(path):
            _list_files(path, result)


def mount_usb():

    devices = list_media_devices()
    found = []
    for device in devices:
        mount(device)
        if is_mounted(device):
            _list_files(get_media_path(device), found)
            if len(found) > 0:
                return True
            else:
                unmount(device)
    return False


def rewrite_dhcpdc_conf(interface, address=None, netmask=None, router=None):

    start_tag = "# ***** begin ishiki templated static ip for %s *****" % interface
    end_tag = "# ***** end ishiki templated static ip for %s *****" % interface

    template = """

%s
interface %s
static ip_address=%s/%s
static routers=%s
static domain_name_servers=8.8.8.8 8.8.4.4
%s

"""

    attr = (start_tag, interface, address, netmask, router, end_tag)

    with open("/etc/dhcpcd.conf", "r") as f:
        current_config = f.read()

    if start_tag in current_config:
        config = current_config[:current_config.find(start_tag)] + current_config[
                                                                   current_config.find(end_tag) + len(end_tag):]
    else:
        config = current_config

    if address:
        config = config + template % attr

    ## remove too much white space
    while "\n\n\n" in config:
        config = config.replace("\n\n\n", "\n\n")

    with open("/etc/dhcpcd.conf", "w") as f:
        f.write(config)


def set_ap_dhcpdc_conf(interface, address=None, netmask=None):

    start_tag = "# ***** begin ishiki templated static ip for %s *****" % interface
    end_tag = "# ***** end ishiki templated static ip for %s *****" % interface

    template = """

%s
interface %s
static ip_address=%s/%s
nohook wpa_supplicant
%s

"""

    attr = (start_tag, interface, address, netmask, end_tag)

    with open("/etc/dhcpcd.conf", "r") as f:
        current_config = f.read()

    if start_tag in current_config:
        config = current_config[:current_config.find(start_tag)] + current_config[
                                                                   current_config.find(end_tag) + len(end_tag):]
    else:
        config = current_config

    if address:
        config = config + template % attr

    ## remove too much white space
    while "\n\n\n" in config:
        config = config.replace("\n\n\n", "\n\n")

    with open("/etc/dhcpcd.conf", "w") as f:
        f.write(config)


def set_ip_address(interface, address=None, netmask=None, router=None):

    if address:
        print("Bootstrap: Setting a static ip address of %s for %s" % (address, interface))
    else:
        print("Bootstrap: Setting %s to use DHCP" % interface)
    rewrite_dhcpdc_conf(interface, address=address, netmask=netmask, router=router)
    cmd = "sudo ip addr flush dev %s" % interface
    subprocess.call(cmd, shell=True)


if __name__ == '__main__':
    start()
