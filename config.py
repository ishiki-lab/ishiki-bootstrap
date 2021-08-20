try:
    from config_local import (NEW_PASSWORD,
                              NEW_USERNAME,
                              NEW_HOSTNAME,
                              ORIGINAL_HOSTNAME,
                              ORIGINAL_USERNAME,
                              ORIGINAL_PASSWORD,
                              ACCESS_IP,
                              DEVICE_CERT_NAME,
                              TUNNEL_CERT_NAME
                              )

except Exception as e:
    print("ERROR: you have to add a file called config_local.py next to this file with the above values")