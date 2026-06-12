"""Die "Taster"-Webseite (View).

Bewusst von der Server-Logik getrennt: hier steht nur das HTML/CSS/JS.
Die Seite holt sich den Ampelzustand per fetch von ``/status`` und zeigt
ihn live an (optionale Anforderung "Zustand auf der Webseite"). Die
Anforderungs-Buttons funktionieren auch ohne JavaScript als normale Links.
"""

PAGE = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ampelsteuerung</title>
  <style>
    body { font-family: sans-serif; text-align: center; background: #222; color: #eee; }
    h1 { margin-top: 1em; }
    .lights { display: flex; justify-content: center; gap: 3em; margin: 1.5em 0; }
    .light { background: #111; padding: 12px; border-radius: 12px; }
    .light h2 { font-size: 1em; margin: 0 0 8px; }
    .lamp { width: 46px; height: 46px; border-radius: 50%; margin: 8px auto; background: #333; }
    .lamp.red.on { background: #e53935; }
    .lamp.yellow.on { background: #fdd835; }
    .lamp.green.on { background: #43a047; }
    .state { font-size: 1.1em; margin-bottom: 1em; }
    a.btn { display: inline-block; background: #1565c0; color: #fff; text-decoration: none;
            padding: 14px 24px; border-radius: 8px; font-size: 1.1em; margin: 6px; }
    a.btn:active { background: #0d47a1; }
    a.btn.car { background: #455a64; }
    a.btn.car:active { background: #263238; }
  </style>
</head>
<body>
  <h1>Ampelsteuerung</h1>

  <div class="lights">
    <div class="light">
      <h2>Auto</h2>
      <div class="lamp red"    id="car-red"></div>
      <div class="lamp yellow" id="car-yellow"></div>
      <div class="lamp green"  id="car-green"></div>
    </div>
    <div class="light">
      <h2>Fussgänger</h2>
      <div class="lamp red"    id="ped-red"></div>
      <div class="lamp yellow" id="ped-yellow"></div>
      <div class="lamp green"  id="ped-green"></div>
    </div>
  </div>

  <p class="state">Zustand: <span id="state">...</span></p>

  <p>
    <a class="btn" href="/request/pedestrian" id="request-ped">Fussgänger: Grün anfordern</a>
    <a class="btn car" href="/request/car" id="request-car">Auto: Grün anfordern</a>
  </p>

  <script>
    const PATTERN = {
      RED:        [1,0,0], RED_YELLOW: [1,1,0],
      GREEN:      [0,0,1], YELLOW:     [0,1,0], OFF: [0,0,0]
    };
    function apply(prefix, phase) {
      const p = PATTERN[phase] || PATTERN.OFF;
      document.getElementById(prefix+'-red').classList.toggle('on', !!p[0]);
      document.getElementById(prefix+'-yellow').classList.toggle('on', !!p[1]);
      document.getElementById(prefix+'-green').classList.toggle('on', !!p[2]);
    }
    async function refresh() {
      try {
        const r = await fetch('/status');
        const s = await r.json();
        apply('car', s.car);
        apply('ped', s.pedestrian);
        let hint = '';
        if (s.pedestrian_requested) hint = ' (Fussgänger angefordert)';
        else if (s.car_requested) hint = ' (Auto angefordert)';
        document.getElementById('state').textContent = s.state + hint;
      } catch (e) { /* Pico evtl. kurz beschaeftigt -> naechster Versuch */ }
    }
    // Buttons per fetch, damit die Seite nicht neu laedt.
    function wire(id, url) {
      document.getElementById(id).addEventListener('click', function (ev) {
        ev.preventDefault();
        fetch(url).then(refresh);
      });
    }
    wire('request-ped', '/request/pedestrian');
    wire('request-car', '/request/car');
    setInterval(refresh, 1000);
    refresh();
  </script>
</body>
</html>
"""
