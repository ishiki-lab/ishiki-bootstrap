# ishiki-bootstrap
Script and resources to build the ishiki sd card image

## Install using prepared image

### Get and burn OS image

* Get the latest image from lush_sd_images in the secrets folder
* Get [Etcher](https://www.balena.io/etcher/) to burn it with
* Burn image to a mini SD card for use in Pi


### Boot it up

* Put the sd card in the pi
* Plug the USB drive into the pi
* Turn pi on
* Wait
* You might need to restart it the first time if it doesn't find the wifi


## Create a Fresh Raspian Base Image

### Get and burn OS image

* Get the [latest raspian image](https://downloads.raspberrypi.org/raspbian_lite_latest)
* Get [Etcher](https://www.balena.io/etcher/) to burn it with
* Burn image to mini SD card for use in Pi

### Configure Pi for wifi/ssh access

Raspbian has some built in magic to help configure sd cards directly.
Mount the flashed SD card on your PC and add two files to the boot folder

* An empty file called `ssh`, this will turn on sshd
* Copy the `wpa_supplicant.conf` file from the `boot` folder of this repo and update it with the SSID and psk of your local wifi.
* Determine the ip address of the pi, either by booting with a screen attatched,
working on a network where the host broadcast works or other devious means.
  * More info [here](https://www.raspberrypi.org/documentation/remote-access/ip-address.md)
  * You can also connect to the pi via a direct connection from your computer's ethernet port. This works best on Linux systems and YMMV!
  * If things are looking weird and connections aren't working, you may need to assign your host machine (i.e. not the Pi) a static IP, like [this](https://askubuntu.com/questions/282569/link-local-connection-to-device-not-working)


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
* Run `fab prepare --screen=<screen_name>`. screen_name can be `waveshare`, `kedei` or `tf_e_ink`,
* Wait for pi to reboot and settle down. NB the current build may take a long time building libsodium from source - just wait.
* Run second part of build (mode can be dev or prod) `fab finish --mode=<mode> --screen=<screen_name>`. mode can be either `dev` or `prod`, screen_name can be `waveshare` or `kedei`,
* Wait for pi to finish installing things and shut itself down
* Remove the sd card from pi and take a copy of the image with `dd` something
 like `sudo dd if=/dev/rdisk2 of=/Users/paul/Documents/lush_prod.img bs=1M` but with a path on your machine
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
