"""Einstiegspunkt der Ampelsteuerung (laeuft beim Booten des Pico W).

Hier wird alles zusammengesteckt und die nicht-blockierende Hauptschleife
gestartet. Die Schleife hat nur zwei Aufgaben pro Durchlauf:

    1. controller.update()  -> Lichtzyklus voranbringen
    2. server.poll()        -> wartende Web-Anfrage bedienen

Weil weder der Controller noch der Server blockieren, bleiben Ampel und
Webseite jederzeit reaktionsschnell.
"""

import time

from access_point import start_access_point
from controller import IntersectionController
from web_server import WebServer


def main():
    start_access_point()

    controller = IntersectionController()
    server = WebServer(controller)

    while True:
        controller.update()
        server.poll()
        time.sleep_ms(10)  # kurze Pause, entlastet die CPU minimal


main()
