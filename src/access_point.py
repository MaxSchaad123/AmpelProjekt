"""WLAN Access-Point (AP-Mode) kapseln.

Der Pico W spannt ein eigenes WLAN auf, in das sich Handy/Laptop einbuchen,
um die "Taster"-Webseite zu erreichen. Diese Funktion isoliert den
Netzwerk-Aufbau vom Rest des Programms.
"""

import time

import network

import config


def start_access_point():
    """Startet den AP und liefert die IP-Adresse zurueck."""
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=config.AP_SSID, password=config.AP_PASSWORD)
    ap.active(True)

    # Warten bis der Access-Point wirklich aktiv ist.
    while not ap.active():
        time.sleep(0.1)

    ip = ap.ifconfig()[0]
    print("Access-Point '{}' aktiv -- IP: {}".format(config.AP_SSID, ip))
    return ip
