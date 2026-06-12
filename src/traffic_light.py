"""Hardware-Abstraktion fuer eine einzelne Ampel (3 LEDs: rot, gelb, gruen).

Die Klasse kapselt die drei GPIO-Pins und bietet ein paar gut benannte
Phasen an. Der Rest des Programms muss nie einzelne Pins schalten, sondern
arbeitet nur mit sprechenden Phasen wie ``Phase.RED_YELLOW``. Das haelt die
Logik (Controller/States) sauber von der Hardware getrennt.
"""

from machine import Pin


class Phase:
    """Moegliche Lichtbilder einer Ampel (als Konstanten / Enum-Ersatz)."""

    RED = "RED"                # rot
    RED_YELLOW = "RED_YELLOW"  # rot + orange (Wechsel rot -> gruen)
    GREEN = "GREEN"            # gruen
    YELLOW = "YELLOW"          # orange (Wechsel gruen -> rot)
    OFF = "OFF"                # alles aus (z.B. Startzustand)


# Welche LEDs leuchten in welcher Phase? (rot, gelb, gruen) -> 1 = an.
# Diese eine Tabelle ersetzt viele on()/off()-Aufrufe und haelt die
# Lichtbilder konsistent (DRY).
_LED_PATTERN = {
    Phase.RED:        (1, 0, 0),
    Phase.RED_YELLOW: (1, 1, 0),
    Phase.GREEN:      (0, 0, 1),
    Phase.YELLOW:     (0, 1, 0),
    Phase.OFF:        (0, 0, 0),
}


class TrafficLight:
    """Eine Ampel mit rot/gelb/gruen an drei GPIO-Pins."""

    def __init__(self, name, pins):
        """``name`` ist sprechend (z.B. "Auto"), ``pins`` ein Dict aus
        config.py mit den Schluesseln ``red``/``yellow``/``green``."""
        self.name = name
        self._red = Pin(pins["red"], Pin.OUT)
        self._yellow = Pin(pins["yellow"], Pin.OUT)
        self._green = Pin(pins["green"], Pin.OUT)
        self.phase = None
        self.set_phase(Phase.RED)

    def set_phase(self, phase):
        """Schaltet das Lichtbild gemaess Phasen-Tabelle."""
        red_on, yellow_on, green_on = _LED_PATTERN[phase]
        self._red.value(red_on)
        self._yellow.value(yellow_on)
        self._green.value(green_on)
        self.phase = phase
