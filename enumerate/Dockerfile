# From ishiki base

# make the volume directory

# Run the enumeration script

# quit

FROM arupiot/ishiki-base:mini

RUN [ "cross-build-start" ]

RUN mkdir /media/usb

COPY TinkerforgeEnum.py .

ENTRYPOINT ["python3"]
CMD ["TinkerforgeEnum.py"]

RUN [ "cross-build-end" ]