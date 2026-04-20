"""
================================================================================
 API-ROUTEN - Network Operations Dashboard
================================================================================
 Datei:         api/routes.py
 Beschreibung:  Definiert alle API-Endpunkte der Anwendung.
                Enthält Routen für Status-Abfragen, Ping-Tests,
                Systeminformationen und Verbindungs-Logs.
 Autor:         Network Dashboard Team
 Erstellt:      2026-04-10
 Version:       1.0.0
================================================================================
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app

from api.services import NetworkService, SystemService

# Logger für dieses Modul konfigurieren
logger = logging.getLogger(__name__)

# ==============================================================================
# BLUEPRINT-DEFINITION
# ==============================================================================

# API Blueprint erstellen - alle Routen werden unter /api/ registriert
api_blueprint = Blueprint(
    'api',                  # Name des Blueprints
    __name__,               # Import-Name
    url_prefix='/api'       # URL-Präfix für alle Routen
)

# Service-Instanzen (werden bei der ersten Anfrage initialisiert)
_network_service = None
_system_service = None


# ==============================================================================
# SERVICE-INITIALISIERUNG
# ==============================================================================

def _get_network_service() -> NetworkService:
    """
    Gibt die NetworkService-Instanz zurück (Lazy Initialization).

    Erstellt den Service beim ersten Aufruf und verwendet danach
    die gespeicherte Instanz.

    Rückgabe:
        NetworkService: Die initialisierte Service-Instanz.
    """
    global _network_service
    if _network_service is None:
        _network_service = NetworkService(config=current_app.config)
        logger.info("NetworkService erstellt")
    return _network_service


def _get_system_service() -> SystemService:
    """
    Gibt die SystemService-Instanz zurück (Lazy Initialization).

    Erstellt den Service beim ersten Aufruf und verwendet danach
    die gespeicherte Instanz.

    Rückgabe:
        SystemService: Die initialisierte Service-Instanz.
    """
    global _system_service
    if _system_service is None:
        _system_service = SystemService(config=current_app.config)
        logger.info("SystemService erstellt")
    return _system_service


# ==============================================================================
# STATUS-ENDPUNKTE
# ==============================================================================

@api_blueprint.route('/status', methods=['GET'])
def get_status():
    """
    GET /api/status

    Gibt den aktuellen Status aller Standorte zurück.

    Query-Parameter:
        location (str, optional): Filtert nach einem bestimmten Standort.

    Rückgabe:
        JSON: Status-Daten aller oder eines bestimmten Standorts.

    Beispiel-Antwort:
        {
            "success": true,
            "data": {
                "locations": {...},
                "summary": {...},
                "last_update": "2026-04-10T14:30:00"
            }
        }
    """
    try:
        logger.info("GET /api/status aufgerufen")
        service = _get_network_service()

        # Optionaler Filter nach Standort
        location_filter = request.args.get('location', None)

        if location_filter:
            # Einzelnen Standort abfragen
            logger.debug(f"Status für Standort: {location_filter}")
            location_status = service.get_location_status(location_filter)

            if location_status is None:
                return jsonify({
                    'success': False,
                    'error': f"Standort '{location_filter}' nicht gefunden.",
                    'available_locations': list(
                        current_app.config.get('LOCATIONS', {}).keys()
                    ),
                    'timestamp': datetime.now().isoformat(),
                }), 404

            return jsonify({
                'success': True,
                'data': location_status,
                'timestamp': datetime.now().isoformat(),
            })

        # Alle Standorte abfragen
        all_status = service.get_all_status()

        return jsonify({
            'success': True,
            'data': all_status,
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Fehler bei Status-Abfrage: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Interner Serverfehler bei der Status-Abfrage.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


@api_blueprint.route('/status/<location_id>', methods=['GET'])
def get_location_status(location_id):
    """
    GET /api/status/<location_id>

    Gibt den Status eines bestimmten Standorts zurück.

    Parameter:
        location_id (str): Die ID des Standorts (z.B. 'frankfurt', 'wien').

    Rückgabe:
        JSON: Status-Daten des angegebenen Standorts.
    """
    try:
        logger.info(f"GET /api/status/{location_id} aufgerufen")
        service = _get_network_service()

        location_status = service.get_location_status(location_id)

        if location_status is None:
            return jsonify({
                'success': False,
                'error': f"Standort '{location_id}' nicht gefunden.",
                'available_locations': list(
                    current_app.config.get('LOCATIONS', {}).keys()
                ),
                'timestamp': datetime.now().isoformat(),
            }), 404

        return jsonify({
            'success': True,
            'data': location_status,
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Fehler bei Status-Abfrage für {location_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Fehler bei der Status-Abfrage für {location_id}.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


# ==============================================================================
# PING-ENDPUNKTE
# ==============================================================================

@api_blueprint.route('/ping/<location_id>', methods=['GET', 'POST'])
def ping_location(location_id):
    """
    GET/POST /api/ping/<location_id>

    Führt einen Ping-Test für den angegebenen Standort durch.

    Parameter:
        location_id (str): Die ID des Standorts (z.B. 'frankfurt', 'wien').

    Rückgabe:
        JSON: Ping-Ergebnisse mit Latenz, Paketverlust und Status.

    Beispiel-Antwort:
        {
            "success": true,
            "data": {
                "location": "frankfurt",
                "host": "127.0.0.1",
                "status": "success",
                "avg_ms": 5.42,
                "packet_loss": 0.0,
                ...
            }
        }
    """
    try:
        logger.info(f"PING /api/ping/{location_id} aufgerufen")
        service = _get_network_service()

        # Überprüfen, ob der Standort existiert
        locations = current_app.config.get('LOCATIONS', {})
        if location_id not in locations:
            return jsonify({
                'success': False,
                'error': f"Standort '{location_id}' nicht gefunden.",
                'available_locations': list(locations.keys()),
                'timestamp': datetime.now().isoformat(),
            }), 404

        # Ping durchführen
        ping_result = service.ping_host(location_id)

        # Erfolg basierend auf dem Ping-Status bestimmen
        is_success = ping_result.get('status') == 'success'

        return jsonify({
            'success': True,
            'data': ping_result,
            'is_reachable': is_success,
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Fehler beim Ping von {location_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Fehler beim Ping von {location_id}.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


@api_blueprint.route('/ping/<location_id>/history', methods=['GET'])
def get_ping_history(location_id):
    """
    GET /api/ping/<location_id>/history

    Gibt den Ping-Verlauf für einen Standort zurück.

    Parameter:
        location_id (str): Die ID des Standorts.

    Query-Parameter:
        limit (int, optional): Maximale Anzahl der Einträge (Standard: 20).

    Rückgabe:
        JSON: Liste der letzten Ping-Ergebnisse.
    """
    try:
        logger.info(f"GET /api/ping/{location_id}/history aufgerufen")
        service = _get_network_service()

        # Limit-Parameter verarbeiten
        limit = request.args.get('limit', 20, type=int)
        limit = min(max(1, limit), 100)  # Zwischen 1 und 100 begrenzen

        history = service.get_ping_history(location_id, limit=limit)

        return jsonify({
            'success': True,
            'data': {
                'location': location_id,
                'history': history,
                'count': len(history),
                'limit': limit,
            },
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Ping-Verlaufs: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Fehler beim Abrufen des Ping-Verlaufs für {location_id}.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


# ==============================================================================
# SYSTEMINFORMATIONS-ENDPUNKTE
# ==============================================================================

@api_blueprint.route('/systeminfo', methods=['GET'])
def get_system_info():
    """
    GET /api/systeminfo

    Gibt umfassende Systeminformationen zurück.

    Query-Parameter:
        section (str, optional): Filtert nach einer bestimmten Sektion
                                 (z.B. 'cpu', 'memory', 'disk', 'os').

    Rückgabe:
        JSON: Systeminformationen (gefiltert oder vollständig).
    """
    try:
        logger.info("GET /api/systeminfo aufgerufen")
        service = _get_system_service()

        sysinfo = service.get_system_info()

        # Optionaler Filter nach Sektion
        section = request.args.get('section', None)

        if section:
            if section in sysinfo:
                return jsonify({
                    'success': True,
                    'data': {
                        'section': section,
                        'info': sysinfo[section],
                    },
                    'timestamp': datetime.now().isoformat(),
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f"Sektion '{section}' nicht gefunden.",
                    'available_sections': list(sysinfo.keys()),
                    'timestamp': datetime.now().isoformat(),
                }), 404

        return jsonify({
            'success': True,
            'data': sysinfo,
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Fehler bei Systeminfo-Abfrage: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler bei der Abfrage der Systeminformationen.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


@api_blueprint.route('/systeminfo/health', methods=['GET'])
def get_health():
    """
    GET /api/systeminfo/health

    Führt einen Gesundheitscheck des Systems durch.

    Rückgabe:
        JSON: Gesundheitsstatus mit einzelnen Check-Ergebnissen.
    """
    try:
        logger.info("GET /api/systeminfo/health aufgerufen")
        service = _get_system_service()

        health = service.get_health_status()

        # HTTP-Status basierend auf dem Gesundheitsstatus setzen
        http_status = 200
        if health['overall'] == 'critical':
            http_status = 503  # Service Unavailable
        elif health['overall'] == 'warning':
            http_status = 200  # OK, aber mit Warnung

        return jsonify({
            'success': True,
            'data': health,
            'timestamp': datetime.now().isoformat(),
        }), http_status

    except Exception as e:
        logger.error(f"Fehler beim Gesundheitscheck: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Gesundheitscheck.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


# ==============================================================================
# LOG-ENDPUNKTE
# ==============================================================================

@api_blueprint.route('/logs', methods=['GET'])
def get_logs():
    """
    GET /api/logs

    Gibt die letzten Verbindungs-Logs zurück.

    Query-Parameter:
        limit (int, optional): Maximale Anzahl der Einträge (Standard: 50).

    Rückgabe:
        JSON: Liste der letzten Log-Einträge.
    """
    try:
        logger.info("GET /api/logs aufgerufen")
        service = _get_network_service()

        # Limit-Parameter verarbeiten
        limit = request.args.get('limit', 50, type=int)
        limit = min(max(1, limit), 500)

        logs = service.get_connection_logs(limit=limit)

        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'count': len(logs),
                'limit': limit,
            },
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Logs: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Abrufen der Verbindungs-Logs.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


# ==============================================================================
# KONFIGURATIONSENDPUNKTE
# ==============================================================================

@api_blueprint.route('/config/locations', methods=['GET'])
def get_locations_config():
    """
    GET /api/config/locations

    Gibt die Konfiguration aller Standorte zurück.
    Nützlich für die Frontend-Initialisierung der Karte.

    Rückgabe:
        JSON: Standort-Konfigurationen mit Koordinaten und Einstellungen.
    """
    try:
        logger.info("GET /api/config/locations aufgerufen")

        locations = current_app.config.get('LOCATIONS', {})

        # Nur relevante Informationen für das Frontend senden
        frontend_locations = {}
        for loc_id, loc_config in locations.items():
            frontend_locations[loc_id] = {
                'name': loc_config.get('name', loc_id),
                'short_name': loc_config.get('short_name', loc_id),
                'country': loc_config.get('country', ''),
                'country_code': loc_config.get('country_code', ''),
                'latitude': loc_config.get('latitude', 0),
                'longitude': loc_config.get('longitude', 0),
                'status': loc_config.get('status', 'unknown'),
                'marker_color': loc_config.get('marker_color', '#888888'),
                'marker_glow': loc_config.get('marker_glow', False),
                'icon': loc_config.get('icon', 'fa-circle'),
                'team': loc_config.get('team', ''),
                'datacenter': loc_config.get('datacenter', ''),
            }

        # Karten-Konfiguration
        map_config = {
            'center': current_app.config.get('MAP_DEFAULT_CENTER', [49.16, 12.43]),
            'zoom': current_app.config.get('MAP_DEFAULT_ZOOM', 6),
            'min_zoom': current_app.config.get('MAP_MIN_ZOOM', 3),
            'max_zoom': current_app.config.get('MAP_MAX_ZOOM', 18),
            'tile_url': current_app.config.get('MAP_TILE_URL', ''),
            'tile_attribution': current_app.config.get('MAP_TILE_ATTRIBUTION', ''),
        }

        return jsonify({
            'success': True,
            'data': {
                'locations': frontend_locations,
                'map': map_config,
            },
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Fehler bei Konfigurationsabfrage: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler bei der Konfigurationsabfrage.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


@api_blueprint.route('/config/dashboard', methods=['GET'])
def get_dashboard_config():
    """
    GET /api/config/dashboard

    Gibt die Dashboard-Konfiguration zurück.
    Enthält Schwellenwerte, Intervalle und UI-Einstellungen.

    Rückgabe:
        JSON: Dashboard-Konfiguration.
    """
    try:
        logger.info("GET /api/config/dashboard aufgerufen")

        config = {
            'auto_refresh_interval': current_app.config.get('AUTO_REFRESH_INTERVAL', 30),
            'ping_timeout': current_app.config.get('PING_TIMEOUT', 5),
            'ping_count': current_app.config.get('PING_COUNT', 4),
            'thresholds': {
                'ping_warning_ms': current_app.config.get('PING_WARNING_THRESHOLD', 100),
                'ping_error_ms': current_app.config.get('PING_ERROR_THRESHOLD', 500),
                'cpu_warning': current_app.config.get('CPU_WARNING_THRESHOLD', 70),
                'cpu_critical': current_app.config.get('CPU_CRITICAL_THRESHOLD', 90),
                'ram_warning': current_app.config.get('RAM_WARNING_THRESHOLD', 75),
                'ram_critical': current_app.config.get('RAM_CRITICAL_THRESHOLD', 90),
                'disk_warning': current_app.config.get('DISK_WARNING_THRESHOLD', 80),
                'disk_critical': current_app.config.get('DISK_CRITICAL_THRESHOLD', 95),
            }
        }

        return jsonify({
            'success': True,
            'data': config,
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Fehler bei Dashboard-Konfigurationsabfrage: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler bei der Dashboard-Konfigurationsabfrage.',
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
        }), 500


# ==============================================================================
# ERROR HANDLER
# ==============================================================================

@api_blueprint.errorhandler(404)
def api_not_found(error):
    """
    Behandelt 404-Fehler innerhalb des API-Blueprints.

    Parameter:
        error: Der HTTP-Fehler.

    Rückgabe:
        JSON: Standardisierte Fehlerantwort.
    """
    return jsonify({
        'success': False,
        'error': 'Der angeforderte API-Endpunkt wurde nicht gefunden.',
        'status_code': 404,
        'timestamp': datetime.now().isoformat(),
    }), 404


@api_blueprint.errorhandler(405)
def api_method_not_allowed(error):
    """
    Behandelt 405-Fehler (Method Not Allowed) innerhalb des API-Blueprints.

    Parameter:
        error: Der HTTP-Fehler.

    Rückgabe:
        JSON: Standardisierte Fehlerantwort.
    """
    return jsonify({
        'success': False,
        'error': 'Die verwendete HTTP-Methode ist für diesen Endpunkt nicht erlaubt.',
        'status_code': 405,
        'timestamp': datetime.now().isoformat(),
    }), 405


@api_blueprint.errorhandler(500)
def api_internal_error(error):
    """
    Behandelt 500-Fehler (Internal Server Error) innerhalb des API-Blueprints.

    Parameter:
        error: Der HTTP-Fehler.

    Rückgabe:
        JSON: Standardisierte Fehlerantwort.
    """
    logger.error(f"Interner Serverfehler: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'error': 'Ein interner Serverfehler ist aufgetreten.',
        'status_code': 500,
        'timestamp': datetime.now().isoformat(),
    }), 500
