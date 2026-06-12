"""Nicht-blockierender HTTP-Server fuer die "Taster"-Webseite.

Wichtig fuer die Architektur: der Server-Socket ist auf ``setblocking(False)``
gesetzt. ``poll()`` wird in der Hauptschleife neben ``controller.update()``
aufgerufen und kehrt sofort zurueck, wenn gerade kein Client wartet. So
laeuft der Lichtzyklus ungestoert weiter, waehrend der Webserver bedient
wird -- anders als bei einem klassischen blockierenden ``accept()``.

Routing (alles GET, damit es per Link/fetch funktioniert):
    /                      -> HTML-Seite
    /request/pedestrian    -> Fussgaenger-Wunsch setzen, dann Status als JSON
    /request/car           -> Auto-Wunsch setzen, dann Status als JSON
    /status                -> aktueller Ampelzustand als JSON
"""

import socket

import config
from web_page import PAGE


class WebServer:
    def __init__(self, controller):
        self._controller = controller
        addr = socket.getaddrinfo("0.0.0.0", config.WEB_PORT)[0][-1]
        self._sock = socket.socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(addr)
        self._sock.listen(1)
        self._sock.setblocking(False)  # <- macht poll() nicht-blockierend
        print("Webserver laeuft auf Port", config.WEB_PORT)

    def poll(self):
        """Bearbeitet hoechstens eine wartende Verbindung und kehrt sofort
        zurueck. Bei keinem Client wirft accept() OSError(EAGAIN)."""
        try:
            client, _ = self._sock.accept()
        except OSError:
            return  # gerade kein Client -> weiter im Takt

        try:
            client.setblocking(True)
            request = client.recv(1024)
            path = self._parse_path(request)
            self._route(client, path)
        except OSError as e:
            print("Web-Fehler:", e)
        finally:
            client.close()

    # -- intern -------------------------------------------------------------
    @staticmethod
    def _parse_path(request):
        """Holt den Pfad aus der ersten Request-Zeile ("GET /pfad HTTP/1.1")."""
        try:
            first_line = request.decode().split("\r\n", 1)[0]
            return first_line.split(" ")[1]
        except (IndexError, UnicodeError):
            return "/"

    def _route(self, client, path):
        if path == "/status":
            self._send_json(client, self._controller.status())
        elif path == "/request/pedestrian":
            self._controller.request_pedestrian()
            self._send_json(client, self._controller.status())
        elif path == "/request/car":
            self._controller.request_car()
            self._send_json(client, self._controller.status())
        elif path == "/":
            self._send_html(client, PAGE)
        else:
            self._send(client, "404 Not Found", "text/plain", "Nicht gefunden")

    # -- Antwort-Helfer (DRY) ----------------------------------------------
    def _send(self, client, status, content_type, body):
        client.send("HTTP/1.1 {}\r\n".format(status))
        client.send("Content-Type: {}\r\n".format(content_type))
        client.send("Connection: close\r\n\r\n")
        client.send(body)

    def _send_html(self, client, body):
        self._send(client, "200 OK", "text/html", body)

    def _send_json(self, client, data):
        self._send(client, "200 OK", "application/json", _to_json(data))


def _to_json(data):
    """Mini-JSON-Serializer fuer flache Dicts (str/bool). Vermeidet die
    Abhaengigkeit von ``ujson`` und reicht fuer unsere Statusdaten."""
    parts = []
    for key, value in data.items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = '"{}"'.format(value)
        parts.append('"{}": {}'.format(key, rendered))
    return "{" + ", ".join(parts) + "}"
