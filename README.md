# Network Operations Dashboard

Ein modernes, umfagreiches Dashboard zur Überwachung von Netzwerk-Standorten (Frankfurt und Wien) mit einer interaktiven Karte (Leaflet), Echtzeit-Statusanzeigen, Ping-Funktionen und Systeminformationen.

## Features

*   **Interaktive Echtzeit-Karte:** Leaflet basierte Karte mit CartoDB Dark Matter Theme.
*   **Dynamische Marker:**
    *   Frankfurt (Online): Pulsierender grüner Glow-Effekt, animierter Verbindungsstatus.
    *   Wien (Offline): Roter Marker, offline Status.
*   **Systeminformationen:** Anzeige von CPU, RAM, Festplatte und Netzwerk des Hosts. Echtes Monitoring über `psutil` (falls installiert) oder realistische Simulation als Fallback.
*   **Netzwerk-Werkzeuge:**
    *   Ping-Simulationen inkl. Latenzen, Paketverlust, Jitter und Min/Max-Werten.
    *   Uptime-Monitoring.
*   **Modernes UI/UX:**
    *   Dark Theme, Glassmorphism-Effekte.
    *   Responsive 3-Spalten CSS Grid Layout.
    *   Animierte Toast-Benachrichtigungen.
    *   Aktivitäts-Log.

## Voraussetzungen

*   Python 3.8 oder höher
*   (Optional, aber empfohlen) `pip install psutil` für echte Hardwaredaten anstatt Simulationen.

## Installation & Start

1.  Wechsle in das Verzeichnis:
    ```bash
    cd network-dashboard
    ```

2.  Installiere die Abhängigkeiten:
    ```bash
    pip install -r requirements.txt
    ```

3.  Starte die Flask-Anwendung:
    ```bash
    python app.py
    ```

4.  Öffne den Browser und navigiere zu:
    [http://localhost:5000](http://localhost:5000)

## Projektstruktur

```
network-dashboard/
│
├── app.py                 # Haupteinstiegspunkt (Flask)
├── config.py              # Konfigurationen (Standorte, Thresholds)
├── requirements.txt       # Abhängigkeiten
│
├── api/                   # Backend-Logik
│   ├── __init__.py
│   ├── routes.py          # API Endpunkte (/status, /ping, /systeminfo)
│   └── services.py        # Business Logik (Netzwerk-Tests, psutil)
│
├── static/                # Frontend Assets
│   ├── css/
│   │   ├── main.css       # Design System, Variablen, Reset
│   │   ├── dashboard.css  # Layout, Karten, Footer
│   │   ├── map.css        # Leaflet, Marker Glow-Effekte
│   │   ├── components.css # Buttons, Modals, Toasts
│   │   └── animations.css # CSS Keyframes und Transitions
│   │
│   └── js/
│       ├── utils.js       # Formatierungen
│       ├── api.js         # Fetch-Wrapper
│       ├── notifications.js # Toast-Manager und Log
│       ├── map.js         # Leaflet Integration
│       ├── dashboard.js   # UI-Updates (DOM Manipulation)
│       └── app.js         # App Controller & Events
│
└── templates/             # HTML Templates (Jinja2)
    ├── base.html          # HTML Gerüst (Imports)
    ├── index.html         # Haupt-Layout 
    └── components/
        ├── navbar.html    # Navigation & Header
        └── modals.html    # Modal-Dialoge
```

## Architektur-Entscheidungen

*   **Kein Frontend-Framework (React/Vue/Angular):** Gemäß den Anforderungen wurde reines Vanilla JS zusammen mit dem Flask Jinja2 Template-Engine verwendet. Dies sorgt für hohe Performance und einfache Auslieferung.
*   **Modularität:** Das System ist strikt in Services (`api/services.py`), Routing (`api/routes.py`) und Frontend-Komponenten aufgeteilt, um die Skalierbarkeit für ein umfangreiches Projekt zu gewährleisten.
*   **Lazy Loading / Async Fetch:** Daten werden asynchron geladen, damit das UI zu jedem Zeitpunkt hoch responsiv bleibt (wie beim Ping-Test).
