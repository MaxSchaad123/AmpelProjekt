"""IntersectionController -- nicht-blockierende State-Machine der Kreuzung.

Der Controller besitzt die beiden Ampeln und den aktuellen Zustand. Er wird
aus der Hauptschleife im Takt ``update()`` aufgerufen und treibt damit den
Lichtzyklus voran, ohne jemals zu blockieren. Der Webserver setzt nur den
Wunsch ``request_pedestrian()`` -- die eigentliche Ablauflogik bleibt hier.

Ablauf:
* Nie gleichzeitig gruen: die Zustaende in states.py schalten Auto und
  Fussgaenger immer ueber rot gegeneinander.
* Eine Seite bleibt gruen, bis die andere Seite Gruen anfordert. Auto bleibt
  gruen bis zur Fussgaenger-Anforderung, Fussgaenger bleibt gruen bis zur
  Auto-Anforderung.
"""

import time

import config
import states
from traffic_light import TrafficLight


class IntersectionController:
    def __init__(self):
        self.car = TrafficLight("Auto", config.CAR_PINS)
        self.pedestrian = TrafficLight("Fussgaenger", config.PEDESTRIAN_PINS)

        self.pedestrian_requested = False
        self.car_requested = False

        self._state = states.INITIAL_STATE
        self._entered_at = time.ticks_ms()
        self._state.on_enter(self)

    # -- Schnittstelle fuer den Webserver -----------------------------------
    def request_pedestrian(self):
        """Fussgaenger meldet den Wunsch nach Gruen an."""
        self.pedestrian_requested = True

    def request_car(self):
        """Auto meldet den Wunsch nach Gruen an."""
        self.car_requested = True

    # -- Takt aus der Hauptschleife -----------------------------------------
    def update(self):
        """Einmal pro Schleifendurchlauf aufrufen. Prueft, ob der aktuelle
        Zustand weiterschalten will, und vollzieht den Uebergang."""
        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self._entered_at)

        next_state = self._state.next_state(self, elapsed)
        if next_state is not None:
            self._enter(next_state, now)

    def _enter(self, state, now):
        self._state = state
        self._entered_at = now
        state.on_enter(self)

    # -- Zustand fuer die optionale Web-Anzeige -----------------------------
    def status(self):
        """Momentaufnahme als Dict (fuer die JSON-Statusanzeige)."""
        return {
            "state": self._state.label,
            "car": self.car.phase,
            "pedestrian": self.pedestrian.phase,
            "pedestrian_requested": self.pedestrian_requested,
            "car_requested": self.car_requested,
        }
