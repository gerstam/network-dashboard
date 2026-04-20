"""
================================================================================
 HAUPTANWENDUNG - Network Operations Dashboard
================================================================================
 Datei:         app.py
 Beschreibung:  Haupteinstiegspunkt der Flask-Webanwendung.
                Initialisiert die Flask-App, registriert Blueprints,
                konfiguriert Logging und definiert die Hauptrouten.
 Autor:         Network Dashboard Team
 Erstellt:      2026-04-10
 Version:       1.0.0
 
 Verwendung:
     python app.py
     
 Umgebungsvariablen:
     FLASK_ENV:    Umgebung (development/testing/production)
     FLASK_HOST:   Server-Host (Standard: 0.0.0.0)
     FLASK_PORT:   Server-Port (Standard: 5000)
     SECRET_KEY:   Geheimer Schlüssel für Sessions
     LOG_LEVEL:    Logging-Level (DEBUG/INFO/WARNING/ERROR)
================================================================================
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from flask import Flask, render_template, jsonify, request

# Konfiguration importieren
from config import get_config

# API-Blueprint importieren
from api.routes import api_blueprint
from api.services import NetworkService, SystemService


# ==============================================================================
# LOGGING-KONFIGURATION
# ==============================================================================

def setup_logging(app):
    """
    Konfiguriert das Logging-System für die Anwendung.

    Erstellt sowohl einen Konsolen-Handler als auch einen Datei-Handler
    mit rotierenden Log-Dateien. Die Log-Level werden aus der
    App-Konfiguration gelesen.

    Parameter:
        app (Flask): Die Flask-Anwendung.
    """
    # Log-Verzeichnis erstellen, falls nicht vorhanden
    log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/dashboard.log'))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Log-Level aus Konfiguration lesen
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)

    # Log-Format definieren
    log_format = app.config.get(
        'LOG_FORMAT',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    formatter = logging.Formatter(log_format)

    # Konsolen-Handler konfigurieren
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Datei-Handler mit Rotation konfigurieren
    file_handler = RotatingFileHandler(
        filename=app.config.get('LOG_FILE', 'logs/dashboard.log'),
        maxBytes=app.config.get('LOG_MAX_SIZE', 10 * 1024 * 1024),
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5),
        encoding='utf-8',
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Handler zur App hinzufügen
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)

    # Root-Logger ebenfalls konfigurieren
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level)

    app.logger.info("Logging-System initialisiert")
    app.logger.info(f"Log-Level: {logging.getLevelName(log_level)}")
    app.logger.info(f"Log-Datei: {app.config.get('LOG_FILE', 'logs/dashboard.log')}")


# ==============================================================================
# APP-FACTORY
# ==============================================================================

def create_app(config_name=None):
    """
    Factory-Funktion zum Erstellen der Flask-Anwendung.

    Erstellt und konfiguriert eine neue Flask-Instanz. Verwendet das
    Factory-Pattern, um verschiedene Konfigurationen für Entwicklung,
    Tests und Produktion zu unterstützen.

    Parameter:
        config_name (str, optional): Name der zu verwendenden Konfiguration.
                                     Wird aus FLASK_ENV gelesen, falls nicht angegeben.

    Rückgabe:
        Flask: Die konfigurierte Flask-Anwendung.
    """
    # Flask-App erstellen
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static',
    )

    # Konfiguration laden
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Logging einrichten
    setup_logging(app)

    app.logger.info("=" * 70)
    app.logger.info("  Network Operations Dashboard wird gestartet...")
    app.logger.info("=" * 70)
    app.logger.info(f"  Umgebung: {config_name or os.environ.get('FLASK_ENV', 'development')}")
    app.logger.info(f"  Debug: {app.config.get('DEBUG', False)}")
    app.logger.info(f"  Host: {app.config.get('HOST', '0.0.0.0')}")
    app.logger.info(f"  Port: {app.config.get('PORT', 5000)}")
    app.logger.info("=" * 70)

    # Blueprints registrieren
    _register_blueprints(app)

    # Hauptrouten registrieren
    _register_main_routes(app)

    # Error Handler registrieren
    _register_error_handlers(app)

    # Kontext-Prozessoren registrieren
    _register_context_processors(app)

    app.logger.info("Flask-Anwendung erfolgreich erstellt und konfiguriert")

    return app


# ==============================================================================
# BLUEPRINT-REGISTRIERUNG
# ==============================================================================

def _register_blueprints(app):
    """
    Registriert alle Blueprints bei der Flask-Anwendung.

    Parameter:
        app (Flask): Die Flask-Anwendung.
    """
    app.register_blueprint(api_blueprint)
    app.logger.info("API-Blueprint registriert unter /api/")


# ==============================================================================
# HAUPTROUTEN
# ==============================================================================

def _register_main_routes(app):
    """
    Registriert die Hauptrouten der Anwendung.

    Diese Routen dienen zur Auslieferung der HTML-Seiten
    (Server-Side Rendering).

    Parameter:
        app (Flask): Die Flask-Anwendung.
    """

    @app.route('/')
    def index():
        """
        GET /

        Hauptseite des Dashboards.
        Rendert die index.html-Vorlage mit allen nötigen Kontextdaten.
        Bei Erkennung eines Text-Browsers (wie Lynx) wird das Text-Dashboard gerendert.
        """
        user_agent = request.headers.get('User-Agent', '')
        text_browsers = ('Lynx', 'Links', 'ELinks', 'w3m', 'Wget', 'curl')
        if any(b in user_agent for b in text_browsers):
            app.logger.info("Text-Browser erkannt, leite zum Text-Dashboard um")
            return _render_text_dashboard(app)

        app.logger.info("Hauptseite aufgerufen")

        # Standort-Daten für das Template vorbereiten
        locations = app.config.get('LOCATIONS', {})

        return render_template(
            'index.html',
            title='Network Operations Dashboard',
            locations=locations,
            map_center=app.config.get('MAP_DEFAULT_CENTER', [49.16, 12.43]),
            map_zoom=app.config.get('MAP_DEFAULT_ZOOM', 6),
            auto_refresh=app.config.get('AUTO_REFRESH_INTERVAL', 30),
            current_year=datetime.now().year,
        )

    @app.route('/text')
    def text_dashboard():
        """
        GET /text
        
        Expliziter Endpunkt für das Text-Modus Dashboard (Lynx).
        """
        app.logger.info("Text-Dashboard aufgerufen")
        return _render_text_dashboard(app)

    @app.route('/text/ping/<location_id>')
    def text_ping(location_id):
        """
        GET /text/ping/<location_id>
        
        Führt einen Ping aus und zeigt das Ergebnis im Text-Modus.
        """
        app.logger.info(f"Text-Modus Ping an {location_id}")
        network_service = NetworkService(config=app.config)
        
        locations = app.config.get('LOCATIONS', {})
        if location_id not in locations:
            return render_template(
                'text_ping.html',
                location_name="Unbekannt",
                ping_result={'status': 'error', 'error_message': 'Standort nicht gefunden.', 'location': location_id}
            )
            
        location_name = locations[location_id].get('name', location_id)
        ping_result = network_service.ping_host(location_id)
        
        return render_template(
            'text_ping.html',
            location_name=location_name,
            ping_result=ping_result
        )

    @app.route('/text/sysinfo')
    def text_sysinfo():
        """
        GET /text/sysinfo
        
        Zeigt Systeminformationen im Text-Modus an.
        """
        app.logger.info("Text-Modus Systeminfo aufgerufen")
        system_service = SystemService(config=app.config)
        sysinfo = system_service.get_system_info()
        
        return render_template(
            'text_sysinfo.html',
            sysinfo=sysinfo
        )

    def _render_text_dashboard(app):
        """Hilfsfunktion zum Rendern des Text-Dashboards mit allen nötigen Daten."""
        network_service = NetworkService(config=app.config)
        system_service = SystemService(config=app.config)
        
        status_data = network_service.get_all_status()
        health_data = system_service.get_system_info()
        log_entries = network_service.get_connection_logs(limit=15)
        
        return render_template(
            'text_dashboard.html',
            status_data=status_data,
            health_data=health_data,
            locations=app.config.get('LOCATIONS', {}),
            log_entries=log_entries,
            now=datetime.now(),
            current_year=datetime.now().year
        )

    @app.route('/health')
    def health_check():
        """
        GET /health

        Einfacher Gesundheitscheck-Endpunkt.
        Gibt den Status 200 zurück, wenn die Anwendung läuft.
        """
        return jsonify({
            'status': 'healthy',
            'application': 'Network Operations Dashboard',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
        })

    app.logger.info("Hauptrouten registriert")


# ==============================================================================
# ERROR HANDLER
# ==============================================================================

def _register_error_handlers(app):
    """
    Registriert globale Error Handler für die Anwendung.

    Parameter:
        app (Flask): Die Flask-Anwendung.
    """

    @app.errorhandler(404)
    def page_not_found(error):
        """Behandelt 404-Fehler (Seite nicht gefunden)."""
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'API-Endpunkt nicht gefunden.',
                'path': request.path,
                'timestamp': datetime.now().isoformat(),
            }), 404

        return render_template(
            'index.html',
            title='404 - Seite nicht gefunden',
            locations=app.config.get('LOCATIONS', {}),
            map_center=app.config.get('MAP_DEFAULT_CENTER', [49.16, 12.43]),
            map_zoom=app.config.get('MAP_DEFAULT_ZOOM', 6),
            auto_refresh=app.config.get('AUTO_REFRESH_INTERVAL', 30),
            current_year=datetime.now().year,
            error_message='Die angeforderte Seite wurde nicht gefunden.',
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Behandelt 500-Fehler (Interner Serverfehler)."""
        app.logger.error(f"Interner Serverfehler: {error}", exc_info=True)

        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Interner Serverfehler.',
                'timestamp': datetime.now().isoformat(),
            }), 500

        return render_template(
            'index.html',
            title='500 - Serverfehler',
            locations=app.config.get('LOCATIONS', {}),
            map_center=app.config.get('MAP_DEFAULT_CENTER', [49.16, 12.43]),
            map_zoom=app.config.get('MAP_DEFAULT_ZOOM', 6),
            auto_refresh=app.config.get('AUTO_REFRESH_INTERVAL', 30),
            current_year=datetime.now().year,
            error_message='Ein interner Serverfehler ist aufgetreten.',
        ), 500

    app.logger.info("Error Handler registriert")


# ==============================================================================
# KONTEXT-PROZESSOREN
# ==============================================================================

def _register_context_processors(app):
    """
    Registriert Kontext-Prozessoren, die Variablen in allen Templates
    verfügbar machen.

    Parameter:
        app (Flask): Die Flask-Anwendung.
    """

    @app.context_processor
    def inject_globals():
        """
        Injiziert globale Variablen in alle Templates.

        Rückgabe:
            dict: Variablen, die in allen Templates verfügbar sind.
        """
        return {
            'app_name': 'Network Operations Dashboard',
            'app_version': '1.0.0',
            'current_year': datetime.now().year,
            'now': datetime.now(),
        }

    app.logger.info("Kontext-Prozessoren registriert")


# ==============================================================================
# HAUPTEINSTIEGSPUNKT
# ==============================================================================

# App-Instanz erstellen
app = create_app()

if __name__ == '__main__':
    """
    Startet den Entwicklungsserver.
    
    ACHTUNG: Diesen Server NICHT in der Produktion verwenden!
    Verwende stattdessen einen WSGI-Server wie Gunicorn oder uWSGI.
    """
    print("\n" + "=" * 70)
    print("  [NOC] Network Operations Dashboard")
    print("  " + "-" * 66)
    print(f"  [URL] URL:    http://localhost:{app.config.get('PORT', 5000)}")
    print(f"  [CFG] Debug:  {app.config.get('DEBUG', False)}")
    print(f"  [ENV] Umgebung: {os.environ.get('FLASK_ENV', 'development')}")
    print("=" * 70 + "\n")

    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', True),
    )
