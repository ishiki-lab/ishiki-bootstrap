# ishiki-bootstrap

The ishiki (意識) project aims at providing an open source framework for deploying distributed IoT applications on Raspberry Pi hardware using the [docker](https://www.docker.com/) technology for running containerised applications at the edge and [Portainer](https://www.portainer.io/) for remote docker applications management.

This repository contains scripts and resources to build ishiki SD card images and generate settings files that the devices will use at boot up stage to generate their identities and connect to either or both:
* a toolbox bastion server via SSH 
* a [Portainer](https://www.portainer.io/) server for remote docker container management.

Creating an ishiki SD card image involves the following steps:
1. downloading a [Raspberry Pi OS image](https://www.raspberrypi.org/software/operating-systems/) and flashing it onto an SD card with a tool like [balenaEtcher](https://www.balena.io/etcher/) - it is recommended not to use an SD card bigger than 4Gb in size so that the SD card image isn't bigger than target SD cards (typically SD card larger than 8GB are a good choice for the target Raspberry Pi)
2. adding an empty `ssh` named file and optionally a [wpa_supplicant.conf](boot/wpa_supplicant.conf) file on the boot partition of the SD card to enable WiFi networking
3. inserting the SD card on the target Raspberry Pi device and booting it, noting its IP address
4. copying the `config_local_template.py` file to `config_local.py` and editing the variables according to your needs, for instance using the correct IP address for the target device
5. using `fab ishiki-prepare` to install the host operating system required components, including [docker](https://www.docker.com/)
6. optionally using `rpi-audio-support-install` or `rpi-screen-support-install` to install audio and screen drivers if needed
7. rebooting the device with `fab reboot-now` 
8. using `fab ishiki-finish` to complete the user setup and enhance the security of the host operating system
9. removing the SD card from the Raspberry Pi device and using a tool like [balenaEtcher](https://www.balena.io/etcher/) to generate an image file from the SD card - note that ishiki-prepare has options to allow device bootstrapping using files contained in the `boot` partition on in a USB stick that can be inserted into one of the USB ports of the target Raspberry Pi device

Once an ishiki SD card image is ready, setting up an ishiki IoT device involves the following steps:
1. downloading the relevant SD card image for the target hardware from the [Ishiki G-Drive](https://drive.google.com/drive/folders/1tEcEPm5kBUOxb5QJtNzzRXn4S44mObtE?usp=sharing), or using the SD card image just generated with the previous steps
2. flashing it on an SD card using a tool like [balenaEtcher](https://www.balena.io/etcher/)
3. editing a `settings.json` file or creating a batch of `settings=#.json` files with `fab ishiki-settings` in case you are targeting more than a single device 
4. adding a `settings.json` file to the `boot` partition or to a USB stick depending on how the SD card has been prepared at the `ishiki-prepare` stage and inserting the USB stick into the Raspberry Pi device
5. booting up the Raspberry Pi device and waiting for it to apply the configuration as outlined in the `settings.json` file.

There are two options for bootstrapping a device:
1. using `fab ishiki-finish --target=boot` if the preference is to use the boot partition as the input location where two store the `settings.json` file
2. using `fab ishiki-finish --target=usb` if the preference is to use a USB flash drive as the input location where two store the `settings.json` file

## Available tasks

Invoking the `fab -l` command outputs the available tasks:

```
$ fab -l
 _     _     _ _    _   _                 _       _                   
(_)___| |__ (_) | _(_) | |__   ___   ___ | |_ ___| |_ _ __ __ _ _ __  
| / __| '_ \| | |/ / | | '_ \ / _ \ / _ \| __/ __| __| '__/ _` | '_ \ 
| \__ \ | | | |   <| | | |_) | (_) | (_) | |_\__ \ |_| | | (_| | |_) |
|_|___/_| |_|_|_|\_\_| |_.__/ \___/ \___/ \__|___/\__|_|  \__,_| .__/ 
                                                               |_|    

Available tasks:

  docker-install               Install docker and docker-compose
  download-audio-samples       Download a selection of audio samples to /opt/audio
  ishiki-finish                Finish the ishiki device setup by enhancing security
  ishiki-prepare               Prepare the base ishiki device image
  ishiki-settings              Generate setting files for bootstrapping devices at their first boot
  reboot-now                   Reboot the remote computer
  rpi-audio-support-install    Install audio support drivers (pimoroni or waveshare)
  rpi-screen-support-install   Install screen support drivers (kedei or waveshare)
  sysinfo                      Get the remote device system information
  update-user                  Create the specified new user
```

## Install using an already available SD card image

### Get and flash the OS image

* Get the latest image from the [Ishiki G-Drive](https://drive.google.com/drive/folders/1tEcEPm5kBUOxb5QJtNzzRXn4S44mObtE?usp=sharing).
* Get [Etcher](https://www.balena.io/etcher/) to flash it with
* Flash the image to a mini SD card for use in Raspberry Pi


### Boot it up

TODO: add the boot vs USB process

* Put the SD card in the Raspberry Pi
* Plug the USB drive into the Raspberry Pi
* Turn the Raspberry Pi on
* Wait
* You might need to restart it the first time if it doesn't find the WiFi


## Create a Fresh Raspian Base Image

### Get and burn OS image

* Get the [latest raspian image](https://downloads.raspberrypi.org/raspbian_lite_latest)
* Get [Etcher](https://www.balena.io/etcher/) to burn it with
* Burn image to mini SD card for use in Pi

### Configure Pi for wifi/ssh access

Raspbian has some built in magic to help configure sd cards directly.
Mount the flashed SD card on your PC and add two files to the boot folder

* An empty file called `ssh`, this will turn on sshd
* Copy the `wpa_supplicant.conf` file from the `boot` folder of this repo and update it with the ssis and psk of your local wifi.
* Determine the ip address of the pi, either by booting with a screen attatched,
working on a network where the host broadcast works or other devious means.


### Install local requirements

* Clone this repo locally
* Create python 3 virtualenv
* Install requirements.txt: `pip install -r requirements.txt`

### Configure card build

for ishiki card

* Copy `config_local.py` from secrets into the root of the repo
* Edit your new local `config_local.py` to add the ip address of the pi
* Copy the whole folder `secrets` in next to the root of this repo

for lushroom card

* Rename config_local_lush.py to config_local.py
* Manually edit the USERNAME at the top of bootstrap.bootstrap.py to "lush"
* Edit your new local `config_local.py` to add the ip address of the pi and a password to use
* create a folder called secrets next to the root of this repo and put the lrpi_id_rsa in there

### Build card with Fabric script

* In terminal cd to the root of this repo
* Run `fab prepare --screen=<screen_name>`. screen_name can be `waveshare` or `kedei`: these screen names refer to the [waveshare 3.5" model B](https://www.waveshare.com/wiki/3.5inch_RPi_LCD_(B)) and [kedei 3.5"](http://kedei.net/raspberry/raspberry.html) touchscreens for the Raspberry Pi.
* Wait for pi to reboot and settle down. NB the current build may take a long time building libsodium from source - just wait.
* Run second part of build (mode can be dev or prod) `fab finish --mode=<mode> --screen=<screen_name>`. mode can be either `dev` or `prod`, screen_name can be `waveshare` or `kedei`,
* Wait for pi to finish installing things and shut itself down
* Remove the sd card from pi and take a copy of the image with `dd` something
 like `sudo dd if=/dev/rdisk2 of=/Users/paul/Documents/lush_prod.img bs=1m` but with a path on your machine
* Optionally shrink the image, for instance with `https://github.com/qrti/shrink`


### Create Lushroom stand alone SD card image

Take the card image as created above and burn to a 16GB card.
Start with your usual dev setting.json but without a docker-compose.yml.
Log in and pull down the docker images used by the stand alone configuration

* lushdigital/lushroom-captive-portal:latest
* dperson/samba:armhf
* lushdigital/lushroom-display:staging
* lushdigital/lushroom-player:staging
* lushdigital/lushroom-brickd:latest

Then shutdown and copy card using dd as above. This is not taking advantage of the resizing for this card.
Ideally It sould be done on a 4GB card with resizing reenabled.

The content of the stand alone `settings.json` is minimal:

```
{
    "name": "lushroom",
    "host_name": "lushroom",
    "time_zone": "Europe/London",
    "captive_portal": true
}
```

and the `docker-compose.yaml` should be:

```
version: '3'

services:
  captive-portal:
    container_name: captive-portal
    image: lushdigital/lushroom-captive-portal:latest
    privileged: true
    network_mode: host
    environment:
      - SSID=lushroom
      - PASSWORD=password
  samba:
    container_name: samba
    image: "dperson/samba:armhf"
    environment:
      - USER=lushroom;password
      - SHARE=media;/media;yes;no;no;lushroom
    ports:
      - 139:139
      - 445:445
    volumes:
       - /media:/media
  display:
    container_name: display
    privileged: true
    network_mode: host
    image: "lushdigital/lushroom-display:staging"
    volumes:
       - /media/usb:/media/usb
       - /dev/fb0:/dev/fb0
       - /dev/input/event0:/dev/input/event0
    restart: always
  player:
    container_name: player
    image: "lushdigital/lushroom-player:staging"
    privileged: true
    ports:
       - 80:80
    volumes:
       - /media/usb:/media/usb
       - /dev/vchiq:/dev/vchiq
       - /opt/vc:/opt/vc
    restart: always
    links:
      - brickd
    environment:
      - BRICKD_HOST=brickd
      - HUE_BRIDGE_ID=099ABE
      - NAME=TEST
  brickd:
    container_name: brickd
    image: "lushdigital/lushroom-brickd:latest"
    privileged: true
    ports:
       - 4223:4223
    restart: always

```
