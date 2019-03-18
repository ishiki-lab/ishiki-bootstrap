FROM balenalib/raspberrypi3-debian:stretch

RUN [ "cross-build-start" ]

RUN apt-get update && apt-get upgrade
RUN apt-get install -y --no-install-recommends apt-utils build-essential python3-dev python3-pip libssl-dev libffi-dev

RUN mkdir /opt/ishiki
COPY src /opt/ishiki/src
WORKDIR /opt/ishiki/src

# install dependencies
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

# run the display command
ENTRYPOINT ["python3"]

RUN [ "cross-build-end" ]