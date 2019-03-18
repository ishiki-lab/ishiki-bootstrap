
from fabric import Connection
from invoke import Responder
from fabric import task
from patchwork.files import append



import os
import logging

logging.raiseExceptions=False

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

from config import (NEW_PASSWORD,
                    NEW_USERNAME,
                    NEW_HOSTNAME,
                    ORIGINAL_HOSTNAME,
                    ORIGINAL_PASSWORD,
                    ORIGINAL_USERNAME,
                    ACCESS_IP,
                    CERTS_NAME
                    )

default_host = ACCESS_IP if ACCESS_IP is not None else "%s.local" % ORIGINAL_HOSTNAME
default_hosts = ["%s:%s" % (default_host, 22)]
renamed_hosts = ["%s.local:%s" % (NEW_HOSTNAME, 22)]

CERTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "secrets"))
DRIVERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "drivers"))

if not os.path.exists(CERTS_DIR):
    raise Exception("couldn't find certs")


def get_cert_path(private=False, certs_name=CERTS_NAME):
    if private:
        return os.path.join(CERTS_DIR, certs_name)
    else:
        return os.path.join(CERTS_DIR, "%s.pub" % certs_name)


cert_path = get_cert_path(private=True)

cert_cxn = Connection(host=default_host,
                      user=NEW_USERNAME,
                      connect_kwargs={
                          "key_filename": cert_path,
                      },
                      port=22)

RASPBIAN_VERSION = "2018-11-13-raspbian-stretch-lite"


@task
def prepare(junk, screen="kedei",  mode="prod"):
    """
    Prepares the base image
    """

    cxn = Connection(host=default_host,
                     user=ORIGINAL_USERNAME,
                     connect_kwargs={"password": ORIGINAL_PASSWORD},
                     port=22)

    create_new_user(cxn)

    new_user_cxn = Connection(host=default_host,
                     user=NEW_USERNAME,
                     connect_kwargs={"password": NEW_PASSWORD},
                     port=22)

    copy_certs(new_user_cxn)

    install_pip(cert_cxn)
    install_extra_libs(cert_cxn)
    install_docker(cert_cxn)
    remove_bloat(cert_cxn)
    configure_rsyslog(cert_cxn)
    daily_reboot(cert_cxn)
    set_hostname(cert_cxn)
    if mode == "prod":
        set_ssh_config(cert_cxn)
        reduce_writes(cert_cxn)
    elif mode == "dev":
        install_samba(cert_cxn)
        set_ssh_config_dev(cert_cxn)
    else:
        raise NotImplementedError("no such mode %s" % mode)

    install_screen_drivers(screen)
    cert_cxn.sudo('reboot now')


@task
def finish(junk):
    yes = Responder(pattern=r'\[Y/n\]',
                         response='\n')

    cert_cxn.sudo("apt --fix-broken install", pty=True, watchers=[yes])
    delete_old_user(cert_cxn)
    add_bootstrap(cert_cxn)
    cert_cxn.sudo("sudo python3 /opt/ishiki/bootstrap/clean_wifi.py")
    cert_cxn.sudo('shutdown now')


######################################################################

def install_screen_drivers(screen_name):

    if screen_name == "waveshare":
        install_waveshare_drivers(cert_cxn)
        config_filename = "waveshare_config.txt"
        _add_config_file(cert_cxn, config_filename, "/boot/config.txt", "root")
    elif screen_name == "kedei":
        install_kedei_drivers(cert_cxn)
        config_filename = "kedei_config.txt"
    else:
        config_filename = "config.txt"


def delete_old_user(cxn):
    cxn.sudo("deluser %s" % ORIGINAL_USERNAME)


def create_new_user(cxn):

    sudopass = Responder(pattern=r'UNIX password:',
                         response='%s\n' % NEW_PASSWORD)

    accept = Responder(pattern=r'\[\]:',
                         response='\n')

    yes = Responder(pattern=r'\[Y/n\]',
                         response='\n')

    cxn.sudo("adduser %s" % NEW_USERNAME, pty=True, watchers=[sudopass, accept, yes])

    # make sudo
    cxn.sudo("usermod -aG sudo %s" % NEW_USERNAME)

    # sudo without password
    append_text(cxn, "/etc/sudoers.d/%s-nopasswd" % NEW_USERNAME, "%s ALL=(ALL) NOPASSWD:ALL" % NEW_USERNAME)

    cxn.sudo("sudo chmod 644 /etc/sudoers.d/%s-nopasswd" % NEW_USERNAME)


def append_text(cxn, file_path, text):
    cxn.sudo('echo "%s" | sudo tee -a %s' % (text, file_path))


def configure_rsyslog(cxn):
    _add_config_file(cxn, "rsyslog.conf", "/etc/rsyslog.conf", "root", chmod="644")


def daily_reboot(cxn):
    append_text(cxn, "/etc/crontab", "0 4    * * *   root    /sbin/shutdown -r +5")


def copy_certs(cxn):
    cxn.run("mkdir /home/%s/.ssh" % NEW_USERNAME)
    cxn.run("chmod 700 /home/%s/.ssh" % NEW_USERNAME)
    cert_path = get_cert_path()
    cxn.put(cert_path, "/home/%s/.ssh/authorized_keys" % NEW_USERNAME)
    cxn.run("chmod 600 /home/%s/.ssh/authorized_keys" % NEW_USERNAME)


def set_ssh_config(cxn):
    _add_config_file(cxn, "sshd_config", "/etc/ssh/sshd_config", "root", chmod="600")
    cxn.sudo("systemctl restart ssh")


def set_ssh_config_dev(cxn):
    _add_config_file(cxn, "sshd_config_dev", "/etc/ssh/sshd_config", "root", chmod="600")
    cxn.sudo("systemctl restart ssh")


def install_pip(cxn):
    cxn.sudo("apt-get update")
    cxn.sudo("apt-get install -y curl")
    cxn.sudo("curl --silent --show-error --retry 5 https://bootstrap.pypa.io/" "get-pip.py | sudo python3")


def install_samba(cxn):
    cxn.sudo("apt-get -y install samba")
    _add_config_file(cxn, "smb.conf", "/etc/samba/smb.conf", "root")
    cxn.sudo("/etc/init.d/samba restart")
    cxn.sudo("smbpasswd -a %s" % NEW_PASSWORD)


def install_extra_libs(cxn):
    cxn.sudo("apt-get update")
    cxn.sudo("apt-get -y install git cmake ntp autossh libxi6")
    cxn.sudo("pip install pyudev")
    cxn.sudo("pip install pyroute2")


def install_docker(cxn):

    # install docker
    cxn.sudo("curl -sSL get.docker.com | sh")

    # fix the docker host in json problem
    _add_config_file(cxn, "docker.service", "/lib/systemd/system/docker.service", "root", chmod=755)

    # config deamon
    _add_config_file(cxn, "daemon.json", "/etc/docker/daemon.json", "root")

    # sets up service
    cxn.sudo("systemctl enable docker")
    # sudo("groupadd docker")
    # allows users to use to use docker
    cxn.sudo("usermod -aG docker %s" % NEW_USERNAME)
    # installs docker compose
    cxn.sudo("pip install docker-compose")


def remove_bloat(cxn):
    cxn.sudo('apt update')
    cxn.sudo("apt-get -y remove --purge libreoffice*")
    cxn.sudo("apt-get -y remove --purge wolfram*")
    cxn.sudo("apt-get -y remove modemmanager")
    cxn.sudo("apt-get -y remove --purge minecraft*")
    cxn.sudo("apt-get -y purge --auto-remove scratch")
    cxn.sudo("dpkg --remove flashplugin-installer")
    cxn.sudo("apt-get clean")
    cxn.sudo("apt-get autoremove")


def set_hostname(cxn):
    cxn.sudo("sed -i 's/%s/%s/g' /etc/hostname" % (ORIGINAL_HOSTNAME, NEW_HOSTNAME))
    cxn.sudo("sed -i 's/%s/%s/g' /etc/hosts" % (ORIGINAL_HOSTNAME, NEW_HOSTNAME))
    cxn.sudo("hostname %s" % NEW_HOSTNAME)



def _add_config_file(cxn, name, dst, owner, chmod=None):

    cxn.put("config_files/%s" % name, "put_temp")
    cxn.sudo("cp put_temp %s" % dst)
    cxn.sudo("rm put_temp")
    if chmod is not None:
        cxn.sudo("chmod %s %s" % (chmod, dst))
    cxn.sudo("chown %s %s" % (owner, dst))
    cxn.sudo("chgrp %s %s" % (owner, dst))


def _add_software_file(cxn, name, dst, owner, chmod=755):

    cxn.put("bootstrap/%s" % name, "put_temp")
    cxn.sudo("mv put_temp %s" % dst)
    cxn.sudo("chmod %s %s" % (chmod, dst))
    cxn.sudo("chown %s %s" % (owner, dst))
    cxn.sudo("chgrp %s %s" % (owner, dst))


def _put_file(cxn, src, dst, owner, chmod=None):
    cxn.put(src, "put_temp")
    cxn.sudo("mv put_temp %s" % dst)
    if chmod is not None:
        cxn.sudo("chmod %s %s" % (chmod, dst))
    cxn.sudo("chown %s %s" % (owner, dst))
    cxn.sudo("chgrp %s %s" % (owner, dst))


def reboot(cxn):
    print('System reboot')
    cxn.sudo('reboot now')
#
# def shutdown():
#     print('shutdown')
#     sudo('shutdown now')
#
# def halt():
#     print('System halt')
#     sudo('halt')
#




def reduce_writes(cxn):

    # a set of optimisations from
    # http://www.zdnet.com/article/raspberry-pi-extending-the-life-of-the-sd-card/
    # and
    # https://narcisocerezo.wordpress.com/2014/06/25/create-a-robust-raspberry-pi-setup-for-24x7-operation/

    # minimise writes
    use_ram_partitions(cxn)
    _stop_fsck_running(cxn)
    _remove_swap(cxn)

    # _redirect_logrotate_state()
    # _dont_update_fake_hwclock()
    # _dont_do_man_indexing()

def use_ram_partitions(cxn):

    append_text(cxn, "/etc/fstab", "tmpfs    /tmp    tmpfs    defaults,noatime,nosuid,size=100m    0 0")
    append_text(cxn, "/etc/fstab", "tmpfs    /var/tmp    tmpfs    defaults,noatime,nosuid,size=30m    0 0")
    append_text(cxn, "/etc/fstab", "tmpfs    /var/log    tmpfs    defaults,noatime,nosuid,mode=0755,size=100m    0 0")

#
# def _redirect_logrotate_state():
#     sudo("rm /etc/cron.daily/logrotate")
#     _add_config_file("logrotate", "/etc/cron.daily/logrotate", "root", chmod="755")
#

def _stop_fsck_running(cxn):
    cxn.sudo("tune2fs -c -1 -i 0 /dev/mmcblk0p2")
#
# def _dont_update_fake_hwclock():
#     sudo("rm /etc/cron.hourly/fake-hwclock")
#
# def _dont_do_man_indexing():
#     sudo("rm  /etc/cron.weekly/man-db")
#     sudo("rm  /etc/cron.daily/man-db")


def _remove_swap(cxn):
    cxn.sudo("update-rc.d -f dphys-swapfile remove")
    cxn.sudo("swapoff /var/swap")
    cxn.sudo("rm /var/swap")


def add_bootstrap(cxn):

    cxn.sudo("mkdir -p /opt/ishiki/bootstrap")

    file_names = ["start.sh",
                  "bootstrap.py",
                  "mount.py",
                  "monitor.py",
                  "clean_wifi.py",
                  "resize_once.txt",
                  "tunnel.service.template"
                  ]

    for name in file_names:
        _add_software_file(cxn, name, "/opt/ishiki/bootstrap/%s" % name, "root")

    _add_config_file(cxn, "ishiki-bootstrap.service", "/etc/systemd/system/ishiki-bootstrap.service", "root", chmod=755)

    # sets up service
    cxn.sudo("systemctl enable ishiki-bootstrap")


#################################################################

def install_waveshare_drivers(cxn):
    waveshare_download_touchscreen_driver(cxn)
    waveshare_install_touchscreen_driver(cxn)


def waveshare_download_touchscreen_driver(cxn):
    cxn.run('git clone https://github.com/waveshare/LCD-show.git')


def waveshare_install_touchscreen_driver(cxn):

    # Enable I2C
    # See https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c#installing-kernel-support-manually

    cxn.sudo('echo "dtparam=i2c1=on" | sudo tee -a /boot/config.txt')
    cxn.sudo('echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt')
    cxn.sudo('echo "i2c-bcm2708" | sudo tee -a /etc/modules')
    cxn.sudo('echo "i2c-dev" | sudo tee -a /etc/modules')

    # Disable Serial Console
    cxn.sudo('sudo sed -i \'s/console=serial0,115200//\' /boot/cmdline.txt')
    cxn.sudo('sudo sed -i \'s/console=ttyAMA0,115200//\' /boot/cmdline.txt')
    cxn.sudo('sudo sed -i \'s/kgdboc=ttyAMA0,115200//\' /boot/cmdline.txt')

    yes = Responder(pattern=r'\[Y/n\]',
                         response='\n')

    cxn.run('cd LCD-show ; sudo ./LCD35B-show-V2', watchers=[yes])
    print('Installing new kernel for Waveshare touchscreen driver completed')


def install_kedei_drivers(cxn):
    cxn.sudo("mkdir -p /opt/kedei")

    tar_file_path = os.path.join(DRIVERS_DIR, "LCD_show_v6_1_3.tar.gz")
    if os.path.exists(tar_file_path):
        # copy from local dir
        _put_file(cxn, tar_file_path, "/opt/kedei/LCD_show_v6_1_3.tar.gz", "root")
    else:
        # download
        cxn.sudo('sh -c "cd /opt/kedei; wget http://www.kedei.net/raspberry/v6_1/LCD_show_v6_1_3.tar.gz"')

    # untar
    cxn.sudo('sh -c "cd /opt/kedei; tar zxvf /opt/kedei/LCD_show_v6_1_3.tar.gz"')
    cxn.sudo("rm /opt/kedei/LCD_show_v6_1_3.tar.gz")
    kedei_install_new_kernel(cxn)


def kedei_install_new_kernel(cxn):

    print('Installing new kernel for Kedei touchscreen driver')

    # Enable I2C
    # See https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c#installing-kernel-support-manually
    cxn.sudo('echo "dtparam=i2c1=on" | sudo tee -a /boot/config.txt')
    cxn.sudo('echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt')
    cxn.sudo('echo "i2c-bcm2708" | sudo tee -a /etc/modules')
    cxn.sudo('echo "i2c-dev" | sudo tee -a /etc/modules')

    # Disable Serial Console
    cxn.sudo('sudo sed -i \'s/console=serial0,115200//\' /boot/cmdline.txt')
    cxn.sudo('sudo sed -i \'s/console=ttyAMA0,115200//\' /boot/cmdline.txt')
    cxn.sudo('sudo sed -i \'s/kgdboc=ttyAMA0,115200//\' /boot/cmdline.txt')

    cxn.sudo('sh -c "cd /opt/kedei/LCD_show_v6_1_3; cp -v ./lcd_35_v/kernel.img /boot/kernel.img"')
    cxn.sudo('sh -c "cd /opt/kedei/LCD_show_v6_1_3; cp -v ./lcd_35_v/kernel7.img /boot/"')
    cxn.sudo('sh -c "cd /opt/kedei/LCD_show_v6_1_3; cp -v ./lcd_35_v/*.dtb /boot/"')
    cxn.sudo('sh -c "cd /opt/kedei/LCD_show_v6_1_3; cp -v ./lcd_35_v/overlays/*.dtb* /boot/overlays/"')
    cxn.sudo('sh -c "cd /opt/kedei/LCD_show_v6_1_3; cp -v -rf ./lcd_35_v/lib/* /lib/"')

    cxn.sudo('apt-mark hold raspberrypi-kernel')
    print('Installing new kernel for Kedei touchscreen driver completed')
