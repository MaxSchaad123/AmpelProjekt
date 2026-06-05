import socket
import network
import machine
import time
from utime import sleep

# =====================
# WLAN (AP MODE)
# =====================
ap = network.WLAN(network.AP_IF)
ap.config(essid="AmpelPico", password="12345678")
ap.active(True)

time.sleep(2)

while not ap.active():
    pass

print("AP gestartet:", ap.ifconfig())

# =====================
# AMPEL PINS
# =====================
auto_rot = machine.Pin(6, machine.Pin.OUT)
auto_gelb = machine.Pin(7, machine.Pin.OUT)
auto_gruen = machine.Pin(8, machine.Pin.OUT)

ped_rot = machine.Pin(18, machine.Pin.OUT)
ped_gelb = machine.Pin(19, machine.Pin.OUT)
ped_gruen = machine.Pin(20, machine.Pin.OUT)

# =====================
# ZUSTÄNDE
# =====================
auto_wunsch = False
ped_wunsch = False

# =====================
# HELFER
# =====================
def alles_rot():
    auto_rot.on()
    auto_gelb.off()
    auto_gruen.off()

    ped_rot.on()
    ped_gelb.off()
    ped_gruen.off()


def auto_gruen_phase():
    alles_rot()
    sleep(1)

    auto_rot.off()
    auto_gelb.on()
    sleep(1)

    auto_gelb.off()
    auto_gruen.on()


def ped_gruen_phase():
    alles_rot()
    sleep(1)

    ped_rot.off()
    ped_gelb.on()
    sleep(1)

    ped_gelb.off()
    ped_gruen.on()


# =====================
# WEB SERVER
# =====================
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

print("Server läuft auf", addr)

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Ampel Steuerung</title>
</head>
<body>
    <h1>Ampel Steuerung</h1>

    <p><a href="/auto">Auto Grün anfordern</a></p>
    <p><a href="/ped">Fussgänger Grün anfordern</a></p>

</body>
</html>
"""

# =====================
# LOOP
# =====================
while True:
    cl = None
    try:
        cl, addr = s.accept()
        request = cl.recv(1024).decode()

        if "/auto" in request:
            auto_wunsch = True

        if "/ped" in request:
            ped_wunsch = True

        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
        cl.send(response)
        cl.close()

        # =====================
        # LOGIK
        # =====================
        if ped_wunsch:
            ped_gruen_phase()
            sleep(5)
            ped_wunsch = False
            auto_wunsch = False

        elif auto_wunsch:
            auto_gruen_phase()
            sleep(5)
            auto_wunsch = False

        else:
            alles_rot()

    except Exception as e:
        if cl:
            try:
                cl.close()
            except:
                pass
        print("Fehler:", e)