"""
================================================================================
 API-SERVICES - Network Operations Dashboard
================================================================================
 Datei:         api/services.py
 Beschreibung:  Service-Klassen für die Geschäftslogik der API.
                Enthält Netzwerk-Dienste (Ping, Traceroute, DNS-Lookup) und
                System-Dienste (CPU, RAM, Festplatte, Betriebssystem-Infos).
 Autor:         Network Dashboard Team
 Erstellt:      2026-04-10
 Version:       1.0.0
================================================================================
"""

import os
import sys
import time
import random
import socket
import platform
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Versuche psutil zu importieren, falls verfügbar
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Logger für dieses Modul konfigurieren
logger = logging.getLogger(__name__)


# ==============================================================================
# NETZWERK-SERVICE
# ==============================================================================

class NetworkService:
    """
    Service-Klasse für alle Netzwerk-bezogenen Operationen.

    Diese Klasse bietet Methoden zum Pingen von Hosts, zur DNS-Auflösung
    und zur Simulation von Netzwerk-Antworten. Sie unterstützt sowohl
    echte Netzwerk-Operationen als auch simulierte Daten für
    Demonstrationszwecke.

    Attribute:
        config (dict): Konfigurationseinstellungen aus der App-Konfiguration.
        ping_history (dict): Verlauf der Ping-Ergebnisse pro Standort.
        max_history_size (int): Maximale Anzahl gespeicherter Ping-Ergebnisse.
    """

    def __init__(self, config=None):
        """
        Initialisiert den Netzwerk-Service.

        Parameter:
            config (dict, optional): Konfigurationsobjekt der Flask-App.
        """
        self.config = config or {}
        self.ping_history = {
            'frankfurt': [],
            'wien': [],
        }
        self.max_history_size = 100
        self._connection_logs = []
        self._max_log_entries = 500

        logger.info("NetworkService initialisiert")

    # --------------------------------------------------------------------------
    # PING-FUNKTIONEN
    # --------------------------------------------------------------------------

    def ping_host(self, location_id: str) -> Dict[str, Any]:
        """
        Führt einen ECHTEN Ping-Test für einen bestimmten Standort durch.

        Verwendet den Betriebssystem-Befehl 'ping' via subprocess, um einen
        realen ICMP-Ping an die konfigurierte IP-Adresse zu senden.
        Parst die Ausgabe des Ping-Befehls, um Latenz, Paketverlust etc. zu
        extrahieren.

        Parameter:
            location_id (str): Die ID des Standorts ('frankfurt' oder 'wien').

        Rückgabe:
            dict: Ein Dictionary mit den Ping-Ergebnissen.
        """
        logger.info(f"Ping-Anfrage für Standort: {location_id}")

        # Standort-Konfiguration laden
        locations = self.config.get('LOCATIONS', {})
        location = locations.get(location_id)

        if not location:
            logger.warning(f"Unbekannter Standort: {location_id}")
            return self._create_error_response(
                location_id,
                'unknown',
                f"Unbekannter Standort: {location_id}"
            )

        # IP-Adresse des Standorts ermitteln
        host = location.get('ip_address', '127.0.0.1')
        ping_count = self.config.get('PING_COUNT', 4)
        ping_timeout = self.config.get('PING_TIMEOUT', 5)

        # Echten Ping durchführen
        result = self._execute_real_ping(location_id, host, ping_count, ping_timeout)

        # Dynamischen Status des Standorts aktualisieren basierend auf Ping-Ergebnis
        if result['status'] == 'success':
            self._update_location_status(location_id, 'online')
        else:
            self._update_location_status(location_id, 'offline')

        # Ergebnis zur Historie hinzufügen
        self._add_to_history(location_id, result)

        # Log-Eintrag erstellen
        self._add_log_entry(
            'PING',
            location_id,
            f"Ping an {host}: {result['status']} "
            f"(Latenz: {result.get('avg_ms', 0):.1f} ms)"
        )

        return result

    def _update_location_status(self, location_id: str, new_status: str):
        """
        Aktualisiert den Status eines Standorts dynamisch basierend auf
        dem Ergebnis eines echten Ping-Tests.

        Parameter:
            location_id (str): Die Standort-ID.
            new_status (str): Der neue Status ('online' oder 'offline').
        """
        locations = self.config.get('LOCATIONS', {})
        if location_id in locations:
            old_status = locations[location_id].get('status', 'unknown')
            locations[location_id]['status'] = new_status

            # Marker-Glow und Services dynamisch anpassen
            if new_status == 'online':
                locations[location_id]['marker_glow'] = True
                locations[location_id]['icon'] = 'fa-server'
                # Services als 'running' markieren
                for svc in locations[location_id].get('services', []):
                    svc['status'] = 'running'
            else:
                locations[location_id]['marker_glow'] = False
                locations[location_id]['icon'] = 'fa-building'
                # Services als 'stopped' markieren
                for svc in locations[location_id].get('services', []):
                    svc['status'] = 'stopped'

            if old_status != new_status:
                logger.info(
                    f"Status von {location_id} hat sich geändert: "
                    f"{old_status} -> {new_status}"
                )

    def _execute_real_ping(self, location_id: str, host: str,
                           count: int = 4, timeout: int = 5) -> Dict[str, Any]:
        """
        Führt einen echten ICMP-Ping über das Betriebssystem aus.

        Verwendet 'ping' als subprocess und parst die Ausgabe, um
        Latenz-Werte und Paketverlust zu extrahieren.

        Parameter:
            location_id (str): Die Standort-ID.
            host (str): Die IP-Adresse des Hosts.
            count (int): Anzahl der Ping-Pakete.
            timeout (int): Timeout pro Paket in Sekunden.

        Rückgabe:
            dict: Ping-Ergebnisse mit echten Messwerten.
        """
        logger.info(f"Führe echten Ping an {host} durch ({count} Pakete, Timeout: {timeout}s)")

        import re

        try:
            # Ping-Befehl für Windows erstellen
            # -n = Anzahl Pakete, -w = Timeout in Millisekunden
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
            else:
                # Linux/Mac: -c = count, -W = timeout in Sekunden
                cmd = ['ping', '-c', str(count), '-W', str(timeout), host]

            logger.debug(f"Ping-Befehl: {' '.join(cmd)}")

            # Subprocess mit Timeout ausführen
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout * count + 10,  # Gesamtes Timeout
                encoding='cp850'  # Windows-Konsolen-Encoding (Deutsch)
            )

            output = proc.stdout
            logger.debug(f"Ping-Ausgabe:\n{output}")

            # Einzelne Latenzwerte extrahieren (Windows: "Zeit=XXms" oder "time=XXms")
            latencies = []
            # Versuche verschiedene Muster (DE/EN Windows, Linux)
            patterns = [
                r'(?:Zeit|time)[=<](\d+(?:\.\d+)?)\s*ms',   # Windows DE/EN
                r'zeit=(\d+(?:\.\d+)?)\s*ms',                 # Windows DE lowercase
                r'time=(\d+(?:\.\d+)?)\s*ms',                 # Linux/Mac
            ]

            for pattern in patterns:
                found = re.findall(pattern, output, re.IGNORECASE)
                if found:
                    latencies = [float(v) for v in found]
                    break

            # TTL extrahieren
            ttl = 0
            ttl_match = re.search(r'TTL[=:]?\s*(\d+)', output, re.IGNORECASE)
            if ttl_match:
                ttl = int(ttl_match.group(1))

            # Paketverlust bestimmen
            packets_sent = count
            packets_received = len(latencies)
            packet_loss = 0.0

            # Paketverlust aus Ausgabe extrahieren (Windows: "Verloren = X (XX% Verlust)")
            loss_patterns = [
                r'(\d+(?:\.\d+)?)\s*%\s*(?:Verlust|loss)',   # DE/EN
                r'(\d+(?:\.\d+)?)\s*%\s*packet loss',         # Linux
            ]
            for pattern in loss_patterns:
                loss_match = re.search(pattern, output, re.IGNORECASE)
                if loss_match:
                    packet_loss = float(loss_match.group(1))
                    break

            # Fallback: Paketverlust berechnen, falls nicht geparst
            if packet_loss == 0.0 and packets_received < packets_sent:
                packet_loss = round((1 - packets_received / packets_sent) * 100, 1)

            # Status bestimmen
            if packets_received > 0:
                status = 'success'
                min_ms = round(min(latencies), 2)
                max_ms = round(max(latencies), 2)
                avg_ms = round(sum(latencies) / len(latencies), 2)

                # Jitter berechnen
                jitter_ms = 0.0
                if len(latencies) > 1:
                    diffs = [abs(latencies[i] - latencies[i-1])
                             for i in range(1, len(latencies))]
                    jitter_ms = round(sum(diffs) / len(diffs), 2)
            else:
                status = 'timeout'
                min_ms = 0
                max_ms = 0
                avg_ms = 0
                jitter_ms = 0

            result = {
                'location': location_id,
                'host': host,
                'status': status,
                'latency_ms': latencies[-1] if latencies else 0,
                'min_ms': min_ms,
                'max_ms': max_ms,
                'avg_ms': avg_ms,
                'jitter_ms': jitter_ms,
                'packet_loss': packet_loss,
                'packets_sent': packets_sent,
                'packets_received': packets_received,
                'latencies': [round(l, 2) for l in latencies],
                'timestamp': datetime.now().isoformat(),
                'method': 'real',
                'ttl': ttl,
            }

            if status == 'timeout':
                result['error_message'] = (
                    f'Zeitüberschreitung: Host {host} ist nicht erreichbar.'
                )

            logger.info(
                f"Ping-Ergebnis für {location_id}: {status} "
                f"(avg: {avg_ms}ms, loss: {packet_loss}%)"
            )
            return result

        except subprocess.TimeoutExpired:
            logger.error(f"Ping-Prozess Timeout für {host}")
            return {
                'location': location_id,
                'host': host,
                'status': 'timeout',
                'latency_ms': 0,
                'min_ms': 0,
                'max_ms': 0,
                'avg_ms': 0,
                'jitter_ms': 0,
                'packet_loss': 100.0,
                'packets_sent': count,
                'packets_received': 0,
                'latencies': [],
                'timestamp': datetime.now().isoformat(),
                'method': 'real',
                'ttl': 0,
                'error_message': f'Ping-Prozess Timeout nach {timeout * count}s.',
            }
        except Exception as e:
            logger.error(f"Fehler beim Ausführen des Pings an {host}: {e}")
            return self._create_error_response(location_id, host, str(e))

    def _create_error_response(self, location_id: str, host: str, error_msg: str) -> Dict[str, Any]:
        """
        Erstellt eine standardisierte Fehlerantwort für Ping-Anfragen.

        Parameter:
            location_id (str): Die Standort-ID.
            host (str): Die IP-Adresse des Hosts.
            error_msg (str): Die Fehlermeldung.

        Rückgabe:
            dict: Fehlerantwort im Standard-Format.
        """
        return {
            'location': location_id,
            'host': host,
            'status': 'error',
            'latency_ms': 0,
            'min_ms': 0,
            'max_ms': 0,
            'avg_ms': 0,
            'jitter_ms': 0,
            'packet_loss': 100.0,
            'packets_sent': 0,
            'packets_received': 0,
            'latencies': [],
            'timestamp': datetime.now().isoformat(),
            'method': 'error',
            'ttl': 0,
            'error_message': error_msg,
        }

    def _add_to_history(self, location_id: str, result: Dict[str, Any]):
        """
        Fügt ein Ping-Ergebnis zur Historie des entsprechenden Standorts hinzu.

        Die Historie wird auf die konfigurierte maximale Größe begrenzt.
        Ältere Einträge werden automatisch entfernt.

        Parameter:
            location_id (str): Die Standort-ID.
            result (dict): Das hinzuzufügende Ping-Ergebnis.
        """
        if location_id not in self.ping_history:
            self.ping_history[location_id] = []

        # Kompaktes Ergebnis für die Historie erstellen
        history_entry = {
            'timestamp': result.get('timestamp', datetime.now().isoformat()),
            'status': result.get('status', 'unknown'),
            'avg_ms': result.get('avg_ms', 0),
            'packet_loss': result.get('packet_loss', 0),
        }

        self.ping_history[location_id].append(history_entry)

        # Historie auf maximale Größe begrenzen
        if len(self.ping_history[location_id]) > self.max_history_size:
            self.ping_history[location_id] = \
                self.ping_history[location_id][-self.max_history_size:]

    def get_ping_history(self, location_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Gibt die letzten Ping-Ergebnisse für einen Standort zurück.

        Parameter:
            location_id (str): Die Standort-ID.
            limit (int): Maximale Anzahl der zurückgegebenen Ergebnisse.

        Rückgabe:
            list: Liste der letzten Ping-Ergebnisse.
        """
        history = self.ping_history.get(location_id, [])
        return history[-limit:]

    # --------------------------------------------------------------------------
    # STATUS-FUNKTIONEN
    # --------------------------------------------------------------------------

    def get_all_status(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Status aller konfigurierten Standorte zurück.

        Rückgabe:
            dict: Status-Informationen aller Standorte mit:
                - locations (dict): Status-Daten für jeden Standort.
                - summary (dict): Zusammenfassung (online/offline Anzahl).
                - last_update (str): Zeitstempel der letzten Aktualisierung.
        """
        logger.info("Status-Abfrage für alle Standorte")

        locations = self.config.get('LOCATIONS', {})
        status_data = {}
        online_count = 0
        offline_count = 0

        for loc_id, loc_config in locations.items():
            # Status-Informationen für jeden Standort zusammenstellen
            loc_status = {
                'id': loc_id,
                'name': loc_config.get('name', loc_id),
                'short_name': loc_config.get('short_name', loc_id),
                'country': loc_config.get('country', 'Unbekannt'),
                'country_code': loc_config.get('country_code', '??'),
                'status': loc_config.get('status', 'unknown'),
                'description': loc_config.get('description', ''),
                'team': loc_config.get('team', 'Nicht zugewiesen'),
                'datacenter': loc_config.get('datacenter', 'Unbekannt'),
                'ip_address': loc_config.get('ip_address', 'N/A'),
                'latitude': loc_config.get('latitude', 0),
                'longitude': loc_config.get('longitude', 0),
                'marker_color': loc_config.get('marker_color', '#888888'),
                'marker_glow': loc_config.get('marker_glow', False),
                'icon': loc_config.get('icon', 'fa-circle'),
                'services': loc_config.get('services', []),
                'uptime': self._calculate_uptime(loc_id),
                'last_ping': self._get_last_ping(loc_id),
            }

            status_data[loc_id] = loc_status

            # Online/Offline Zähler aktualisieren
            if loc_config.get('status') == 'online':
                online_count += 1
            else:
                offline_count += 1

        # Zusammenfassung erstellen
        total = online_count + offline_count
        health_percentage = (online_count / total * 100) if total > 0 else 0

        return {
            'locations': status_data,
            'summary': {
                'total': total,
                'online': online_count,
                'offline': offline_count,
                'health_percentage': round(health_percentage, 1),
            },
            'last_update': datetime.now().isoformat(),
            'auto_refresh_interval': self.config.get('AUTO_REFRESH_INTERVAL', 30),
        }

    def get_location_status(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt den Status eines einzelnen Standorts zurück.

        Parameter:
            location_id (str): Die Standort-ID.

        Rückgabe:
            dict oder None: Status-Daten des Standorts oder None, falls nicht gefunden.
        """
        all_status = self.get_all_status()
        return all_status['locations'].get(location_id)

    def _calculate_uptime(self, location_id: str) -> Dict[str, Any]:
        """
        Berechnet die simulierte Betriebszeit für einen Standort.

        Parameter:
            location_id (str): Die Standort-ID.

        Rückgabe:
            dict: Betriebszeit-Informationen mit:
                - days (int): Anzahl der Tage.
                - hours (int): Verbleibende Stunden.
                - minutes (int): Verbleibende Minuten.
                - percentage (float): Verfügbarkeit in Prozent.
                - formatted (str): Formatierte Darstellung.
        """
        locations = self.config.get('LOCATIONS', {})
        location = locations.get(location_id, {})

        if location.get('status') == 'online':
            # Echte, fortlaufende Betriebszeit berechnen
            boot_time = location.get('boot_time', 0)
            if boot_time > 0:
                uptime_seconds = time.time() - boot_time
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                seconds = int(uptime_seconds % 60)
            else:
                days = 0
                hours = 0
                minutes = 0
                seconds = 0
            percentage = location.get('availability', 99.9)
        else:
            # Offline-Standort hat keine aktive Betriebszeit
            days = 0
            hours = 0
            minutes = 0
            seconds = 0
            percentage = 0.0

        return {
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'percentage': percentage,
            'formatted': f"{days}d {hours}h {minutes}m {seconds}s",
        }

    def _get_last_ping(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt das letzte Ping-Ergebnis für einen Standort zurück.

        Parameter:
            location_id (str): Die Standort-ID.

        Rückgabe:
            dict oder None: Das letzte Ping-Ergebnis oder None.
        """
        history = self.ping_history.get(location_id, [])
        return history[-1] if history else None

    # --------------------------------------------------------------------------
    # CONNECTION LOG FUNKTIONEN
    # --------------------------------------------------------------------------

    def _add_log_entry(self, log_type: str, location_id: str, message: str):
        """
        Fügt einen Eintrag zum Verbindungs-Log hinzu.

        Parameter:
            log_type (str): Art des Log-Eintrags (z.B. 'PING', 'STATUS').
            location_id (str): Die Standort-ID.
            message (str): Die Log-Nachricht.
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': log_type,
            'location': location_id,
            'message': message,
        }

        self._connection_logs.append(entry)

        # Log auf maximale Größe begrenzen
        if len(self._connection_logs) > self._max_log_entries:
            self._connection_logs = self._connection_logs[-self._max_log_entries:]

    def get_connection_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Gibt die letzten Verbindungs-Log-Einträge zurück.

        Parameter:
            limit (int): Maximale Anzahl der zurückgegebenen Einträge.

        Rückgabe:
            list: Liste der letzten Log-Einträge (neueste zuerst).
        """
        return list(reversed(self._connection_logs[-limit:]))


# ==============================================================================
# SYSTEM-SERVICE
# ==============================================================================

class SystemService:
    """
    Service-Klasse für System-Monitoring und Informationssammlung.

    Diese Klasse sammelt Informationen über das System wie CPU-Auslastung,
    RAM-Nutzung, Festplattenplatz und Betriebssystem-Details. Wenn psutil
    verfügbar ist, werden echte Systemdaten verwendet, andernfalls werden
    die Daten simuliert.

    Attribute:
        config (dict): Konfigurationseinstellungen.
        _cached_sysinfo (dict): Zwischengespeicherte Systeminformationen.
        _cache_timestamp (float): Zeitstempel des letzten Cache-Updates.
        _cache_duration (int): Gültigkeitsdauer des Caches in Sekunden.
    """

    def __init__(self, config=None):
        """
        Initialisiert den System-Service.

        Parameter:
            config (dict, optional): Konfigurationsobjekt der Flask-App.
        """
        self.config = config or {}
        self._cached_sysinfo = None
        self._cache_timestamp = 0
        self._cache_duration = self.config.get('SYSINFO_UPDATE_INTERVAL', 10)
        self._boot_time = time.time()

        logger.info("SystemService initialisiert")

    # --------------------------------------------------------------------------
    # SYSTEM-INFORMATIONEN
    # --------------------------------------------------------------------------

    def get_system_info(self) -> Dict[str, Any]:
        """
        Sammelt umfassende Systeminformationen.

        Gibt zwischengespeicherte Daten zurück, wenn der Cache noch gültig ist.
        Ansonsten werden die Informationen neu gesammelt.

        Rückgabe:
            dict: Umfassende Systeminformationen mit:
                - os (dict): Betriebssystem-Details.
                - cpu (dict): Prozessor-Informationen und Auslastung.
                - memory (dict): Arbeitsspeicher-Nutzung.
                - disk (dict): Festplatten-Nutzung.
                - network (dict): Netzwerk-Informationen.
                - python (dict): Python-Version und -Pfad.
                - uptime (dict): System-Betriebszeit.
                - timestamp (str): Zeitstempel der Datensammlung.
        """
        # Cache-Prüfung
        current_time = time.time()
        if (self._cached_sysinfo and
                current_time - self._cache_timestamp < self._cache_duration):
            logger.debug("Systeminformationen aus Cache zurückgegeben")
            return self._cached_sysinfo

        logger.info("Systeminformationen werden gesammelt...")

        # Alle Systeminformationen sammeln
        sysinfo = {
            'os': self._get_os_info(),
            'cpu': self._get_cpu_info(),
            'memory': self._get_memory_info(),
            'disk': self._get_disk_info(),
            'network': self._get_network_info(),
            'python': self._get_python_info(),
            'uptime': self._get_uptime_info(),
            'processes': self._get_process_info(),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'psutil' if PSUTIL_AVAILABLE else 'simulated',
        }

        # Cache aktualisieren
        self._cached_sysinfo = sysinfo
        self._cache_timestamp = current_time

        return sysinfo

    def _get_os_info(self) -> Dict[str, Any]:
        """
        Sammelt Betriebssystem-Informationen.

        Rückgabe:
            dict: OS-Details wie Name, Version, Plattform und Architektur.
        """
        return {
            'system': platform.system(),
            'node_name': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor() or 'N/A',
            'platform': platform.platform(),
            'architecture': platform.architecture()[0],
            'python_build': platform.python_build()[0],
        }

    def _get_cpu_info(self) -> Dict[str, Any]:
        """
        Sammelt CPU-Informationen und aktuelle Auslastung.

        Verwendet psutil für echte Daten oder simuliert realistische Werte.

        Rückgabe:
            dict: CPU-Details wie Kernanzahl, Frequenz und Auslastung.
        """
        if PSUTIL_AVAILABLE:
            try:
                # Echte CPU-Daten mit psutil sammeln
                cpu_freq = psutil.cpu_freq()
                cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)

                return {
                    'physical_cores': psutil.cpu_count(logical=False) or 0,
                    'logical_cores': psutil.cpu_count(logical=True) or 0,
                    'frequency_mhz': {
                        'current': round(cpu_freq.current, 2) if cpu_freq else 0,
                        'min': round(cpu_freq.min, 2) if cpu_freq else 0,
                        'max': round(cpu_freq.max, 2) if cpu_freq else 0,
                    },
                    'usage_percent': psutil.cpu_percent(interval=0.1),
                    'usage_per_core': cpu_percent_per_core,
                    'load_average': self._get_load_average(),
                    'status': self._get_cpu_status(psutil.cpu_percent(interval=0.1)),
                }
            except Exception as e:
                logger.error(f"Fehler beim Sammeln der CPU-Daten: {e}")
                return self._simulate_cpu_info()
        else:
            return self._simulate_cpu_info()

    def _simulate_cpu_info(self) -> Dict[str, Any]:
        """
        Simuliert CPU-Informationen für Systeme ohne psutil.

        Rückgabe:
            dict: Simulierte CPU-Daten mit realistischen Werten.
        """
        cores = 8
        usage = round(random.uniform(15, 65), 1)
        per_core = [round(random.uniform(5, 80), 1) for _ in range(cores)]

        return {
            'physical_cores': cores // 2,
            'logical_cores': cores,
            'frequency_mhz': {
                'current': round(random.uniform(2400, 3800), 2),
                'min': 800.0,
                'max': 4200.0,
            },
            'usage_percent': usage,
            'usage_per_core': per_core,
            'load_average': [
                round(random.uniform(0.5, 3.0), 2),
                round(random.uniform(0.5, 2.5), 2),
                round(random.uniform(0.5, 2.0), 2),
            ],
            'status': self._get_cpu_status(usage),
        }

    def _get_cpu_status(self, usage: float) -> str:
        """
        Bestimmt den CPU-Status basierend auf der Auslastung.

        Parameter:
            usage (float): CPU-Auslastung in Prozent.

        Rückgabe:
            str: Status ('normal', 'warning' oder 'critical').
        """
        warning_threshold = self.config.get('CPU_WARNING_THRESHOLD', 70)
        critical_threshold = self.config.get('CPU_CRITICAL_THRESHOLD', 90)

        if usage >= critical_threshold:
            return 'critical'
        elif usage >= warning_threshold:
            return 'warning'
        return 'normal'

    def _get_load_average(self) -> List[float]:
        """
        Gibt die Systemlast zurück (1, 5 und 15 Minuten Durchschnitt).

        Rückgabe:
            list: Systemlast-Werte als Liste mit 3 Elementen.
        """
        try:
            if hasattr(os, 'getloadavg'):
                load = os.getloadavg()
                return [round(l, 2) for l in load]
        except Exception:
            pass

        # Simulierte Werte für Windows und andere Systeme
        return [
            round(random.uniform(0.5, 3.0), 2),
            round(random.uniform(0.5, 2.5), 2),
            round(random.uniform(0.5, 2.0), 2),
        ]

    def _get_memory_info(self) -> Dict[str, Any]:
        """
        Sammelt Arbeitsspeicher-Informationen.

        Rückgabe:
            dict: RAM-Details wie Gesamtspeicher, Nutzung und Status.
        """
        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                swap = psutil.swap_memory()

                return {
                    'total_gb': round(mem.total / (1024 ** 3), 2),
                    'available_gb': round(mem.available / (1024 ** 3), 2),
                    'used_gb': round(mem.used / (1024 ** 3), 2),
                    'free_gb': round(mem.free / (1024 ** 3), 2),
                    'usage_percent': mem.percent,
                    'swap': {
                        'total_gb': round(swap.total / (1024 ** 3), 2),
                        'used_gb': round(swap.used / (1024 ** 3), 2),
                        'free_gb': round(swap.free / (1024 ** 3), 2),
                        'usage_percent': swap.percent,
                    },
                    'status': self._get_memory_status(mem.percent),
                }
            except Exception as e:
                logger.error(f"Fehler beim Sammeln der RAM-Daten: {e}")
                return self._simulate_memory_info()
        else:
            return self._simulate_memory_info()

    def _simulate_memory_info(self) -> Dict[str, Any]:
        """
        Simuliert Arbeitsspeicher-Informationen.

        Rückgabe:
            dict: Simulierte RAM-Daten mit realistischen Werten.
        """
        total_gb = 32.0
        usage_percent = round(random.uniform(35, 70), 1)
        used_gb = round(total_gb * usage_percent / 100, 2)
        free_gb = round(total_gb - used_gb, 2)
        available_gb = round(free_gb + random.uniform(1, 3), 2)

        return {
            'total_gb': total_gb,
            'available_gb': available_gb,
            'used_gb': used_gb,
            'free_gb': free_gb,
            'usage_percent': usage_percent,
            'swap': {
                'total_gb': 16.0,
                'used_gb': round(random.uniform(0.5, 4.0), 2),
                'free_gb': round(random.uniform(12.0, 15.5), 2),
                'usage_percent': round(random.uniform(3, 25), 1),
            },
            'status': self._get_memory_status(usage_percent),
        }

    def _get_memory_status(self, usage: float) -> str:
        """
        Bestimmt den RAM-Status basierend auf der Auslastung.

        Parameter:
            usage (float): RAM-Auslastung in Prozent.

        Rückgabe:
            str: Status ('normal', 'warning' oder 'critical').
        """
        warning_threshold = self.config.get('RAM_WARNING_THRESHOLD', 75)
        critical_threshold = self.config.get('RAM_CRITICAL_THRESHOLD', 90)

        if usage >= critical_threshold:
            return 'critical'
        elif usage >= warning_threshold:
            return 'warning'
        return 'normal'

    def _get_disk_info(self) -> Dict[str, Any]:
        """
        Sammelt Festplatten-Informationen.

        Rückgabe:
            dict: Festplatten-Details wie Speicherplatz und Nutzung.
        """
        if PSUTIL_AVAILABLE:
            try:
                partitions = []
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        partitions.append({
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total_gb': round(usage.total / (1024 ** 3), 2),
                            'used_gb': round(usage.used / (1024 ** 3), 2),
                            'free_gb': round(usage.free / (1024 ** 3), 2),
                            'usage_percent': round(usage.percent, 1),
                        })
                    except PermissionError:
                        continue

                # Gesamtnutzung der ersten Partition als Hauptwert
                main_usage = partitions[0]['usage_percent'] if partitions else 0

                return {
                    'partitions': partitions,
                    'total_partitions': len(partitions),
                    'main_usage_percent': main_usage,
                    'status': self._get_disk_status(main_usage),
                }
            except Exception as e:
                logger.error(f"Fehler beim Sammeln der Festplatten-Daten: {e}")
                return self._simulate_disk_info()
        else:
            return self._simulate_disk_info()

    def _simulate_disk_info(self) -> Dict[str, Any]:
        """
        Simuliert Festplatten-Informationen.

        Rückgabe:
            dict: Simulierte Festplatten-Daten.
        """
        usage_percent = round(random.uniform(30, 65), 1)
        total = 512.0
        used = round(total * usage_percent / 100, 2)

        partitions = [
            {
                'device': 'C:',
                'mountpoint': 'C:\\',
                'fstype': 'NTFS',
                'total_gb': total,
                'used_gb': used,
                'free_gb': round(total - used, 2),
                'usage_percent': usage_percent,
            },
            {
                'device': 'D:',
                'mountpoint': 'D:\\',
                'fstype': 'NTFS',
                'total_gb': 1024.0,
                'used_gb': round(random.uniform(100, 600), 2),
                'free_gb': round(random.uniform(400, 900), 2),
                'usage_percent': round(random.uniform(10, 60), 1),
            }
        ]

        return {
            'partitions': partitions,
            'total_partitions': len(partitions),
            'main_usage_percent': usage_percent,
            'status': self._get_disk_status(usage_percent),
        }

    def _get_disk_status(self, usage: float) -> str:
        """
        Bestimmt den Festplatten-Status basierend auf der Auslastung.

        Parameter:
            usage (float): Festplatten-Auslastung in Prozent.

        Rückgabe:
            str: Status ('normal', 'warning' oder 'critical').
        """
        warning_threshold = self.config.get('DISK_WARNING_THRESHOLD', 80)
        critical_threshold = self.config.get('DISK_CRITICAL_THRESHOLD', 95)

        if usage >= critical_threshold:
            return 'critical'
        elif usage >= warning_threshold:
            return 'warning'
        return 'normal'

    def _get_network_info(self) -> Dict[str, Any]:
        """
        Sammelt Netzwerk-Informationen.

        Rückgabe:
            dict: Netzwerk-Details wie Hostname, IP-Adresse und Interfaces.
        """
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            hostname = 'unknown'
            local_ip = '127.0.0.1'

        network_info = {
            'hostname': hostname,
            'local_ip': local_ip,
            'interfaces': [],
        }

        if PSUTIL_AVAILABLE:
            try:
                # Netzwerk-Interfaces auslesen
                addrs = psutil.net_if_addrs()
                stats = psutil.net_if_stats()
                io_counters = psutil.net_io_counters(pernic=True)

                for iface_name, iface_addrs in addrs.items():
                    iface_info = {
                        'name': iface_name,
                        'addresses': [],
                        'is_up': False,
                        'speed_mbps': 0,
                    }

                    # Adressen sammeln
                    for addr in iface_addrs:
                        if addr.family == socket.AF_INET:
                            iface_info['addresses'].append({
                                'type': 'IPv4',
                                'address': addr.address,
                                'netmask': addr.netmask,
                            })

                    # Status prüfen
                    if iface_name in stats:
                        iface_info['is_up'] = stats[iface_name].isup
                        iface_info['speed_mbps'] = stats[iface_name].speed

                    # I/O-Statistiken
                    if iface_name in io_counters:
                        io = io_counters[iface_name]
                        iface_info['bytes_sent'] = io.bytes_sent
                        iface_info['bytes_recv'] = io.bytes_recv
                        iface_info['packets_sent'] = io.packets_sent
                        iface_info['packets_recv'] = io.packets_recv

                    if iface_info['addresses']:
                        network_info['interfaces'].append(iface_info)
            except Exception as e:
                logger.error(f"Fehler beim Sammeln der Netzwerk-Daten: {e}")
        else:
            # Simulierte Netzwerk-Interfaces
            network_info['interfaces'] = [
                {
                    'name': 'Ethernet',
                    'addresses': [{'type': 'IPv4', 'address': local_ip, 'netmask': '255.255.255.0'}],
                    'is_up': True,
                    'speed_mbps': 1000,
                    'bytes_sent': random.randint(1000000, 9999999999),
                    'bytes_recv': random.randint(1000000, 9999999999),
                    'packets_sent': random.randint(10000, 999999),
                    'packets_recv': random.randint(10000, 999999),
                },
            ]

        return network_info

    def _get_python_info(self) -> Dict[str, Any]:
        """
        Sammelt Python-Umgebungsinformationen.

        Rückgabe:
            dict: Python-Details wie Version, Pfad und installierte Pakete.
        """
        return {
            'version': platform.python_version(),
            'implementation': platform.python_implementation(),
            'compiler': platform.python_compiler(),
            'executable': sys.executable,
            'path': sys.path[:5],  # Nur die ersten 5 Pfade
            'prefix': sys.prefix,
        }

    def _get_uptime_info(self) -> Dict[str, Any]:
        """
        Berechnet die System-Betriebszeit.

        Rückgabe:
            dict: Betriebszeit-Informationen.
        """
        if PSUTIL_AVAILABLE:
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
            except Exception:
                uptime_seconds = time.time() - self._boot_time
        else:
            uptime_seconds = time.time() - self._boot_time

        # Betriebszeit in Tage, Stunden, Minuten umrechnen
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)

        return {
            'total_seconds': int(uptime_seconds),
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'formatted': f"{days}d {hours}h {minutes}m {seconds}s",
            'boot_time': datetime.fromtimestamp(
                self._boot_time if not PSUTIL_AVAILABLE else
                (psutil.boot_time() if PSUTIL_AVAILABLE else self._boot_time)
            ).isoformat(),
        }

    def _get_process_info(self) -> Dict[str, Any]:
        """
        Sammelt Informationen über laufende Prozesse.

        Rückgabe:
            dict: Prozess-Informationen mit Top-Prozessen nach CPU und RAM.
        """
        if PSUTIL_AVAILABLE:
            try:
                total_processes = len(psutil.pids())
                top_cpu = []
                top_memory = []

                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        info = proc.info
                        top_cpu.append(info)
                        top_memory.append(info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Nach CPU-Nutzung sortieren (Top 5)
                top_cpu = sorted(top_cpu, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:5]

                # Nach RAM-Nutzung sortieren (Top 5)
                top_memory = sorted(top_memory, key=lambda x: x.get('memory_percent', 0), reverse=True)[:5]

                return {
                    'total': total_processes,
                    'top_cpu': top_cpu,
                    'top_memory': top_memory,
                }
            except Exception as e:
                logger.error(f"Fehler beim Sammeln der Prozess-Daten: {e}")
                return self._simulate_process_info()
        else:
            return self._simulate_process_info()

    def _simulate_process_info(self) -> Dict[str, Any]:
        """
        Simuliert Prozess-Informationen.

        Rückgabe:
            dict: Simulierte Prozess-Daten.
        """
        processes = [
            {'pid': 4, 'name': 'System', 'cpu_percent': round(random.uniform(0, 5), 1), 'memory_percent': round(random.uniform(0.1, 0.5), 1)},
            {'pid': 1234, 'name': 'python.exe', 'cpu_percent': round(random.uniform(1, 15), 1), 'memory_percent': round(random.uniform(1, 5), 1)},
            {'pid': 5678, 'name': 'chrome.exe', 'cpu_percent': round(random.uniform(2, 20), 1), 'memory_percent': round(random.uniform(3, 12), 1)},
            {'pid': 9012, 'name': 'explorer.exe', 'cpu_percent': round(random.uniform(0, 3), 1), 'memory_percent': round(random.uniform(1, 3), 1)},
            {'pid': 3456, 'name': 'svchost.exe', 'cpu_percent': round(random.uniform(0, 8), 1), 'memory_percent': round(random.uniform(0.5, 2), 1)},
        ]

        return {
            'total': random.randint(150, 350),
            'top_cpu': sorted(processes, key=lambda x: x['cpu_percent'], reverse=True),
            'top_memory': sorted(processes, key=lambda x: x['memory_percent'], reverse=True),
        }

    # --------------------------------------------------------------------------
    # HEALTH-CHECK
    # --------------------------------------------------------------------------

    def get_health_status(self) -> Dict[str, Any]:
        """
        Führt einen umfassenden Gesundheitscheck des Systems durch.

        Überprüft CPU, RAM und Festplatte und gibt einen Gesamtstatus zurück.

        Rückgabe:
            dict: Gesundheitsstatus mit:
                - overall (str): Gesamtstatus ('healthy', 'warning', 'critical').
                - checks (dict): Einzelne Check-Ergebnisse.
                - timestamp (str): Zeitstempel.
        """
        sysinfo = self.get_system_info()

        checks = {
            'cpu': {
                'status': sysinfo['cpu']['status'],
                'value': sysinfo['cpu']['usage_percent'],
                'unit': '%',
                'message': f"CPU-Auslastung: {sysinfo['cpu']['usage_percent']}%",
            },
            'memory': {
                'status': sysinfo['memory']['status'],
                'value': sysinfo['memory']['usage_percent'],
                'unit': '%',
                'message': f"RAM-Auslastung: {sysinfo['memory']['usage_percent']}%",
            },
            'disk': {
                'status': sysinfo['disk']['status'],
                'value': sysinfo['disk']['main_usage_percent'],
                'unit': '%',
                'message': f"Festplatten-Auslastung: {sysinfo['disk']['main_usage_percent']}%",
            },
        }

        # Gesamtstatus bestimmen (schlechtester Einzelstatus)
        statuses = [c['status'] for c in checks.values()]
        if 'critical' in statuses:
            overall = 'critical'
        elif 'warning' in statuses:
            overall = 'warning'
        else:
            overall = 'healthy'

        return {
            'overall': overall,
            'checks': checks,
            'timestamp': datetime.now().isoformat(),
        }
