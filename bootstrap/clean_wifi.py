
def remove():

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "r") as f:
        t = f.read()

    t = t[:t.find("network")]

    print(t)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
        f.write(t)

if __name__ == '__main__':
    remove()