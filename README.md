# Ampelsteuerung (Raspberry Pi Pico W)

Ampelsteuerung für zwei Ampeln (Auto + Fussgänger) auf einem Raspberry Pi
Pico W. Der Pico spannt im **AP-Mode** ein eigenes WLAN auf und stellt eine
Webseite bereit, über die Fussgänger Grün anfordern können ("Taster"). Die
Ampeln durchlaufen den vollständigen Lichtzyklus, ohne dass je beide
gleichzeitig grün sind.

## Architektur

Die Steuerung ist in klar getrennte Module aufgeteilt. Jedes Modul hat eine
Verantwortung (Separation of Concerns):

| Datei                | Verantwortung                                              |
|----------------------|------------------------------------------------------------|
| `src/config.py`      | Zentrale Konfiguration: Pins, Zeiten, WLAN (Single Source of Truth) |
| `src/traffic_light.py` | Hardware-Abstraktion einer Ampel (3 LEDs) mit Phasen     |
| `src/states.py`      | Lichtzyklus als **State-Pattern** (jede Phase = ein Objekt) |
| `src/controller.py`  | Nicht-blockierende State-Machine + Anforderungs-Logik      |
| `src/access_point.py`| WLAN Access-Point (AP-Mode) aufsetzen                      |
| `src/web_server.py`  | Nicht-blockierender HTTP-Server + Routing                  |
| `src/web_page.py`    | Die Webseite (View, HTML/CSS/JS)                          |
| `src/main.py`        | Einstiegspunkt: steckt alles zusammen, Hauptschleife       |

### Datenfluss

```
Browser ──HTTP──> web_server ──request_pedestrian()──> controller
                                                          │
                          main-Loop ──update()──> controller ──set_phase()──> traffic_light ──> LEDs
                                                          │
                                                       states (State-Pattern)
```

Der Webserver setzt nur einen *Wunsch*. Die eigentliche Ablauflogik liegt im
Controller, der im Takt der Hauptschleife die State-Machine vorantreibt.

## Eingesetzte Design-Patterns

- **State-Pattern** (`states.py`): Jede Phase des Lichtzyklus ist ein eigenes
  Zustandsobjekt mit `on_enter()` (Lichtbild setzen) und `next_state()`
  (Übergang entscheiden). Der Ablauf ist dadurch als Zustandsdiagramm direkt
  im Code ablesbar und leicht erweiterbar.
- **Nicht-blockierende State-Machine** (`controller.py`): Kein `sleep()` im
  Ablauf. Übergänge werden über `time.ticks_ms()` zeitgesteuert, damit der
  Webserver parallel reaktionsschnell bleibt.
- **Hardware-Abstraktion / Facade** (`traffic_light.py`): Der Rest des
  Programms schaltet nie einzelne Pins, sondern arbeitet mit sprechenden
  Phasen (`Phase.RED_YELLOW`).
- **Single Source of Truth / DRY** (`config.py`, `_LED_PATTERN`,
  `_TimedState`): Pins, Zeiten und Lichtbilder stehen je an genau einer Stelle.

## Lichtzyklus

Vollständiger Zyklus laut Auftrag — gilt für **beide** Ampeln:

- Wechsel rot → grün: `rot` → `rot + orange` → `grün`
- Wechsel grün → rot: `grün` → `orange` → `rot`

**Ablauf:** Jede Seite bleibt grün, bis die *andere* Seite Grün anfordert.
Startzustand ist Auto grün / Fussgänger rot. Fordert ein Fussgänger Grün an,
durchläuft die Autoampel `grün → orange → rot`, danach geht die
Fussgängerampel über `rot → rot+orange → grün` und **bleibt grün**, bis ein
Auto Grün anfordert. Dann läuft der gleiche Wechsel zurück. Es gibt keine
festen Grünzeiten — nur die Übergangsphasen sind zeitgesteuert.

- ✅ Nie gleichzeitig grün (Übergänge laufen immer über Rot).
- ✅ Symmetrische, einfache Logik: zwei Anforderungs-Buttons (Fussgänger / Auto).

Die Dauer der Übergangsphasen wird in [`src/config.py`](src/config.py) eingestellt.

## Verdrahtung

| Ampel        | LED | GPIO (Code) | Pin am Pico |
|--------------|-----|-------------|-------------|
| Auto (1)     | R   | GPIO 6      | Pin 9       |
| Auto (1)     | Y   | GPIO 7      | Pin 10      |
| Auto (1)     | G   | GPIO 8      | Pin 11      |
| Auto (1)     | GND | –           | Pin 8       |
| Fussgänger (2) | R | GPIO 18     | Pin 24      |
| Fussgänger (2) | Y | GPIO 19     | Pin 25      |
| Fussgänger (2) | G | GPIO 20     | Pin 26      |
| Fussgänger (2) | GND | –          | Pin 23      |

## Deployment auf den Pico W

Voraussetzung: VS Code mit der **MicroPico**-Erweiterung (bereits im Projekt
konfiguriert). Die Einstellung `micropico.syncFolder: "src"` sorgt dafür, dass
der **Inhalt** von `src/` ins Wurzelverzeichnis des Pico geladen wird — damit
`main.py` beim Booten automatisch startet.

1. Pico W per USB anschliessen.
2. In VS Code: `MicroPico: Upload project to Pico` ausführen.
3. `MicroPico: Reset > Hard reset` — die Steuerung startet.

### Bedienung

1. Mit WLAN **`AmpelPico`** verbinden (Passwort: `ampel1234`).
2. Im Browser `http://192.168.4.1` öffnen.
3. Auf **„Fussgänger: Grün anfordern"** tippen.

Die Webseite zeigt den aktuellen Zustand beider Ampeln live an (pollt jede
Sekunde `/status`).

## Lokal testen (ohne Hardware)

Die reine Ablauflogik (State-Machine) lässt sich am PC mit Mock-Modulen
prüfen — die Hardware-/Netzwerk-Abhängigkeiten sind sauber gekapselt, sodass
`controller.py` und `states.py` ohne echten Pico durchlaufen.
