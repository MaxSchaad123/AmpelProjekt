"""Lichtzyklus als State-Pattern.

Jeder Zustand der Kreuzung ist ein eigenes Objekt mit zwei Aufgaben:

* ``on_enter``  -> stellt das Lichtbild beider Ampeln ein (einmalig)
* ``next_state``-> entscheidet (nicht-blockierend) ob/wann gewechselt wird

Der Controller haelt nur den aktuellen Zustand und fragt ihn im Takt ab.
Dadurch ist der komplette Ablauf als Zustandsdiagramm direkt im Code
ablesbar und es gibt keine blockierenden ``sleep``-Aufrufe.

Vollstaendiger Zyklus laut Auftrag (gilt fuer beide Ampeln):
    rot -> rot+orange -> grün   und   grün -> orange -> rot

Ablauf-Logik (symmetrisch und einfach):
Eine Seite bleibt grün, bis die *andere* Seite grün anfordert. Auto grün
bleibt also bis zur Fussgänger-Anforderung, Fussgänger grün bleibt bis zur
Auto-Anforderung. Es gibt keine festen grünzeiten.
"""

import config
from traffic_light import Phase


class State:
    """Basisklasse fuer alle Kreuzungs-Zustaende."""

    label = "Unbekannt"  # menschenlesbar fuer die Webseite

    def on_enter(self, controller):
        """Lichtbild setzen. Wird genau einmal beim Eintritt aufgerufen."""
        raise NotImplementedError

    def next_state(self, controller, elapsed_ms):
        """Folgezustand zurueckgeben oder ``None`` wenn verweilt wird."""
        raise NotImplementedError


class _TimedState(State):
    """Hilfsbasis fuer Zustaende, die nach fester Dauer weiterschalten.

    Unterklassen setzen ``duration_ms`` und ``follow_up`` (ein Zustand).
    Spart Wiederholung in den vielen reinen Uebergangsphasen (DRY).
    """

    duration_ms = 0
    # Folgezustand; wird nach den Klassendefinitionen verdrahtet.
    follow_up: "State | None" = None

    def next_state(self, controller, elapsed_ms):
        if elapsed_ms >= self.duration_ms:
            return self.follow_up
        return None


# ---------------------------------------------------------------------------
# Auto faehrt -> bleibt grün, bis Fussgänger anfordern
# ---------------------------------------------------------------------------
class CarGreen(State):
    label = "Auto grün"

    def on_enter(self, controller):
        controller.car.set_phase(Phase.GREEN)
        controller.pedestrian.set_phase(Phase.RED)

    def next_state(self, controller, elapsed_ms):
        if controller.pedestrian_requested:
            # Wunsch wird jetzt bedient -> Flag zuruecksetzen, damit Auto
            # grün danach wieder auf eine frische Anforderung wartet.
            controller.pedestrian_requested = False
            return CAR_YELLOW
        return None


# ---------------------------------------------------------------------------
# Uebergang Auto: grün -> orange -> rot, Sicherheits-Allrot
# ---------------------------------------------------------------------------
class CarYellow(_TimedState):
    label = "Auto orange"
    duration_ms = config.YELLOW_MS

    def on_enter(self, controller):
        controller.car.set_phase(Phase.YELLOW)


class AllRedToPedestrian(_TimedState):
    label = "Allrot"
    duration_ms = config.ALL_RED_MS

    def on_enter(self, controller):
        controller.car.set_phase(Phase.RED)
        controller.pedestrian.set_phase(Phase.RED)


# ---------------------------------------------------------------------------
# Uebergang Fussgänger: rot -> rot+orange -> grün
# ---------------------------------------------------------------------------
class PedestrianRedYellow(_TimedState):
    label = "Fussgänger rot+orange"
    duration_ms = config.RED_YELLOW_MS

    def on_enter(self, controller):
        controller.pedestrian.set_phase(Phase.RED_YELLOW)


# ---------------------------------------------------------------------------
# Fussgänger grün -> bleibt grün, bis die Autos anfordern
# ---------------------------------------------------------------------------
class PedestrianGreen(State):
    label = "Fussgänger grün"

    def on_enter(self, controller):
        controller.pedestrian.set_phase(Phase.GREEN)
        controller.car.set_phase(Phase.RED)

    def next_state(self, controller, elapsed_ms):
        if controller.car_requested:
            controller.car_requested = False
            return PEDESTRIAN_YELLOW
        return None


# ---------------------------------------------------------------------------
# Uebergang Fussgänger: grün -> orange -> rot, dann zurueck zu Auto
# ---------------------------------------------------------------------------
class PedestrianYellow(_TimedState):
    label = "Fussgänger orange"
    duration_ms = config.YELLOW_MS

    def on_enter(self, controller):
        controller.pedestrian.set_phase(Phase.YELLOW)


class AllRedToCar(_TimedState):
    label = "Allrot"
    duration_ms = config.ALL_RED_MS

    def on_enter(self, controller):
        controller.car.set_phase(Phase.RED)
        controller.pedestrian.set_phase(Phase.RED)


class CarRedYellow(_TimedState):
    label = "Auto rot+orange"
    duration_ms = config.RED_YELLOW_MS

    def on_enter(self, controller):
        controller.car.set_phase(Phase.RED_YELLOW)


# ---------------------------------------------------------------------------
# Singleton-Instanzen + Verdrahtung der Uebergaenge.
# (Nach den Klassendefinitionen, damit alle Namen bekannt sind.)
# ---------------------------------------------------------------------------
CAR_GREEN = CarGreen()
CAR_YELLOW = CarYellow()
ALL_RED_TO_PEDESTRIAN = AllRedToPedestrian()
PEDESTRIAN_RED_YELLOW = PedestrianRedYellow()
PEDESTRIAN_GREEN = PedestrianGreen()
PEDESTRIAN_YELLOW = PedestrianYellow()
ALL_RED_TO_CAR = AllRedToCar()
CAR_RED_YELLOW = CarRedYellow()

# Auto-Anforderung -> Fussgänger weicht (grün -> ... -> Auto grün)
CAR_YELLOW.follow_up = ALL_RED_TO_PEDESTRIAN
ALL_RED_TO_PEDESTRIAN.follow_up = PEDESTRIAN_RED_YELLOW
PEDESTRIAN_RED_YELLOW.follow_up = PEDESTRIAN_GREEN
# PEDESTRIAN_GREEN haelt, bis ein Auto anfordert (siehe next_state)
PEDESTRIAN_YELLOW.follow_up = ALL_RED_TO_CAR
ALL_RED_TO_CAR.follow_up = CAR_RED_YELLOW
CAR_RED_YELLOW.follow_up = CAR_GREEN

# Startzustand der Kreuzung.
INITIAL_STATE = CAR_GREEN
