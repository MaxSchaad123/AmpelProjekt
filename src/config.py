"""Zentrale Konfiguration der Ampelsteuerung.

Alle Pin-Belegungen, Zeiten und WLAN-Daten stehen an genau einer Stelle
(Single Source of Truth -> DRY). Wer die Hardware umverdrahtet oder die
Phasen-Dauern anpassen will, aendert nur diese Datei.
"""

# ---------------------------------------------------------------------------
# Pin-Belegung (GPIO-Nummern laut Verdrahtungsplan im Auftrag)
#
#   Ampel          R        Y        G
#   Auto (1)      GPIO 6   GPIO 7   GPIO 8
#   Fussgaenger   GPIO 18  GPIO 19  GPIO 20
# ---------------------------------------------------------------------------
CAR_PINS = {"red": 6, "yellow": 7, "green": 8}
PEDESTRIAN_PINS = {"red": 18, "yellow": 19, "green": 20}

# ---------------------------------------------------------------------------
# Dauer der Uebergangsphasen in Millisekunden
#
# Die State-Machine arbeitet nicht-blockierend mit time.ticks_ms(), darum
# werden alle Zeiten in ms angegeben. Die Gruenphasen selbst haben keine
# feste Dauer: jede Seite bleibt gruen, bis die andere Seite Gruen anfordert.
# ---------------------------------------------------------------------------
YELLOW_MS = 2000            # Gelb-Phase beim Wechsel gruen -> rot
RED_YELLOW_MS = 1000        # Rot+Gelb-Phase beim Wechsel rot -> gruen
ALL_RED_MS = 1000           # Sicherheits-Allrot zwischen den Richtungen

# ---------------------------------------------------------------------------
# WLAN Access-Point (AP-Mode): der Pico spannt ein eigenes Netz auf.
# ---------------------------------------------------------------------------
AP_SSID = "AmpelPico"
AP_PASSWORD = "ampel1234"   # WPA2 verlangt mind. 8 Zeichen
WEB_PORT = 80
