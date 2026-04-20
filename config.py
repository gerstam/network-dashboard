"""
================================================================================
 KONFIGURATIONSDATEI - Network Operations Dashboard
================================================================================
 Datei:         config.py
 Beschreibung:  Zentrale Konfigurationsdatei für die Flask-Anwendung.
                Enthält alle konfigurierbaren Parameter wie Server-Einstellungen,
                Standort-Definitionen, Netzwerk-Timeouts und Logging-Optionen.
 Autor:         Network Dashboard Team
 Erstellt:      2026-04-10
 Version:       1.0.0
================================================================================
"""

import os
import time
from datetime import timedelta


# ==============================================================================
# BASIS-KONFIGURATION
# ==============================================================================

class BaseConfig:
    """
    Basis-Konfigurationsklasse.
    Enthält alle grundlegenden Einstellungen, die in allen Umgebungen
    (Entwicklung, Test, Produktion) verwendet werden.
    """

    # --------------------------------------------------------------------------
    # Flask Grundeinstellungen
    # --------------------------------------------------------------------------
    # Geheimer Schlüssel für Session-Management und CSRF-Schutz
    SECRET_KEY = os.environ.get('SECRET_KEY', 'noc-dashboard-secret-key-2026-change-in-production')

    # Debug-Modus (wird in Unterklassen überschrieben)
    DEBUG = False

    # Testing-Modus (wird in Unterklassen überschrieben)
    TESTING = False

    # --------------------------------------------------------------------------
    # Server-Einstellungen
    # --------------------------------------------------------------------------
    # Host-Adresse, auf der der Server lauscht
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')

    # Port, auf dem der Server lauscht
    PORT = int(os.environ.get('FLASK_PORT', 5000))

    # --------------------------------------------------------------------------
    # Standort-Definitionen
    # --------------------------------------------------------------------------
    # Jeder Standort wird mit seinen geografischen Koordinaten,
    # seinem aktuellen Status und zusätzlichen Metadaten definiert.
    LOCATIONS = {
        'frankfurt': {
            'name': 'Frankfurt am Main',
            'short_name': 'Frankfurt',
            'country': 'Deutschland',
            'country_code': 'DE',
            'latitude': 50.1109,
            'longitude': 8.6821,
            'status': 'online',
            'description': 'Primäres Rechenzentrum - Hauptstandort',
            'team': 'Alpha Team',
            'datacenter': 'Equinix FR5',
            'ip_address': '10.211.32.121',
            'timezone': 'Europe/Berlin',
            'services': [
                {'name': 'Web Server', 'port': 80, 'status': 'running'},
                {'name': 'API Gateway', 'port': 8080, 'status': 'running'},
                {'name': 'Database', 'port': 5432, 'status': 'running'},
                {'name': 'Cache Server', 'port': 6379, 'status': 'running'},
                {'name': 'Message Queue', 'port': 5672, 'status': 'running'},
                {'name': 'Monitoring', 'port': 9090, 'status': 'running'},
            ],
            'boot_time': time.time(),
            'availability': 99.9,
            'marker_color': '#00ff88',
            'marker_glow': True,
            'icon': 'fa-server',
        },
        'wien': {
            'name': 'Wien',
            'short_name': 'Wien',
            'country': 'Österreich',
            'country_code': 'AT',
            'latitude': 48.2082,
            'longitude': 16.3738,
            'status': 'offline',
            'description': 'Sekundäres Rechenzentrum - Partnerstandort',
            'team': 'Beta Team',
            'datacenter': 'Interxion VIE1',
            'ip_address': '10.211.32.68',
            'timezone': 'Europe/Vienna',
            'services': [
                {'name': 'Web Server', 'port': 80, 'status': 'stopped'},
                {'name': 'API Gateway', 'port': 8080, 'status': 'stopped'},
                {'name': 'Database', 'port': 5432, 'status': 'stopped'},
                {'name': 'Cache Server', 'port': 6379, 'status': 'stopped'},
                {'name': 'Message Queue', 'port': 5672, 'status': 'stopped'},
                {'name': 'Monitoring', 'port': 9090, 'status': 'stopped'},
            ],
            'boot_time': 0,
            'availability': 0.0,
            'marker_color': '#ff4455',
            'marker_glow': False,
            'icon': 'fa-building',
        }
    }

    # --------------------------------------------------------------------------
    # Netzwerk-Einstellungen
    # --------------------------------------------------------------------------
    # Timeout für Ping-Anfragen (in Sekunden)
    PING_TIMEOUT = 5

    # Anzahl der Ping-Versuche
    PING_COUNT = 4

    # Maximale Ping-Latenz, ab der eine Warnung ausgelöst wird (in ms)
    PING_WARNING_THRESHOLD = 100

    # Maximale Ping-Latenz, ab der ein Fehler ausgelöst wird (in ms)
    PING_ERROR_THRESHOLD = 500

    # Intervall für automatische Status-Updates (in Sekunden)
    AUTO_REFRESH_INTERVAL = 30

    # --------------------------------------------------------------------------
    # Logging-Einstellungen
    # --------------------------------------------------------------------------
    # Log-Level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Log-Format
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Log-Datei Pfad
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/dashboard.log')

    # Maximale Größe einer Log-Datei (in Bytes) - Standard: 10 MB
    LOG_MAX_SIZE = 10 * 1024 * 1024

    # Anzahl der aufzubewahrenden Log-Dateien
    LOG_BACKUP_COUNT = 5

    # --------------------------------------------------------------------------
    # Cache-Einstellungen
    # --------------------------------------------------------------------------
    # Cache-Typ (simple, redis, memcached)
    CACHE_TYPE = 'simple'

    # Standard Cache-Timeout (in Sekunden)
    CACHE_DEFAULT_TIMEOUT = 60

    # --------------------------------------------------------------------------
    # API Rate Limiting
    # --------------------------------------------------------------------------
    # Maximale Anzahl von API-Anfragen pro Minute
    RATE_LIMIT_PER_MINUTE = 60

    # Maximale Anzahl von Ping-Anfragen pro Minute
    PING_RATE_LIMIT_PER_MINUTE = 10

    # --------------------------------------------------------------------------
    # Dashboard-Einstellungen
    # --------------------------------------------------------------------------
    # Standard-Kartenansicht (Zentrum zwischen Frankfurt und Wien)
    MAP_DEFAULT_CENTER = [49.1596, 12.4279]

    # Standard-Zoom-Level der Karte
    MAP_DEFAULT_ZOOM = 6

    # Minimaler Zoom-Level
    MAP_MIN_ZOOM = 3

    # Maximaler Zoom-Level
    MAP_MAX_ZOOM = 18

    # Karten-Tile-Provider URL
    MAP_TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'

    # Karten-Tile-Attribution
    MAP_TILE_ATTRIBUTION = (
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
        'contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    )

    # --------------------------------------------------------------------------
    # Simulations-Einstellungen
    # --------------------------------------------------------------------------
    # Simulierte Ping-Werte für Frankfurt (in ms)
    SIMULATED_PING_FRANKFURT = {
        'min': 1,
        'max': 15,
        'jitter': 3,
        'packet_loss': 0.0,
    }

    # Simulierte Ping-Werte für Wien (offline)
    SIMULATED_PING_WIEN = {
        'min': 0,
        'max': 0,
        'jitter': 0,
        'packet_loss': 100.0,
    }

    # --------------------------------------------------------------------------
    # System-Monitoring Einstellungen
    # --------------------------------------------------------------------------
    # Intervall für Systeminfo-Updates (in Sekunden)
    SYSINFO_UPDATE_INTERVAL = 10

    # CPU-Auslastungs-Schwellenwerte (in Prozent)
    CPU_WARNING_THRESHOLD = 70
    CPU_CRITICAL_THRESHOLD = 90

    # RAM-Auslastungs-Schwellenwerte (in Prozent)
    RAM_WARNING_THRESHOLD = 75
    RAM_CRITICAL_THRESHOLD = 90

    # Festplatten-Auslastungs-Schwellenwerte (in Prozent)
    DISK_WARNING_THRESHOLD = 80
    DISK_CRITICAL_THRESHOLD = 95


# ==============================================================================
# ENTWICKLUNGS-KONFIGURATION
# ==============================================================================

class DevelopmentConfig(BaseConfig):
    """
    Konfiguration für die Entwicklungsumgebung.
    Aktiviert Debug-Modus und verwendet weniger strenge Einstellungen.
    """
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    RATE_LIMIT_PER_MINUTE = 120
    PING_RATE_LIMIT_PER_MINUTE = 30


# ==============================================================================
# TEST-KONFIGURATION
# ==============================================================================

class TestConfig(BaseConfig):
    """
    Konfiguration für die Testumgebung.
    Aktiviert Testing-Modus und verwendet Mock-Daten.
    """
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    PING_TIMEOUT = 1
    PING_COUNT = 1


# ==============================================================================
# PRODUKTIONS-KONFIGURATION
# ==============================================================================

class ProductionConfig(BaseConfig):
    """
    Konfiguration für die Produktionsumgebung.
    Verwendet strenge Sicherheitseinstellungen.
    """
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SECRET_KEY = os.environ.get('SECRET_KEY', None)

    def __init__(self):
        """Überprüft, ob ein sicherer Secret Key gesetzt wurde."""
        if not self.SECRET_KEY:
            raise ValueError(
                "FEHLER: In der Produktionsumgebung muss die Umgebungsvariable "
                "'SECRET_KEY' gesetzt sein!"
            )


# ==============================================================================
# KONFIGURATIONSZUORDNUNG
# ==============================================================================

# Dictionary zur Zuordnung von Umgebungsnamen zu Konfigurationsklassen
config_map = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config(env_name=None):
    """
    Gibt die passende Konfigurationsklasse basierend auf dem Umgebungsnamen zurück.

    Parameter:
        env_name (str, optional): Name der Umgebung ('development', 'testing', 'production').
                                  Wird aus der Umgebungsvariable FLASK_ENV gelesen,
                                  falls nicht angegeben.

    Rückgabe:
        BaseConfig: Die entsprechende Konfigurationsklasse.
    """
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development')

    return config_map.get(env_name, config_map['default'])
