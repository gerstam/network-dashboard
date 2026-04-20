"""
================================================================================
 API-PAKET - Network Operations Dashboard
================================================================================
 Datei:         api/__init__.py
 Beschreibung:  Initialisierungsdatei für das API-Paket.
                Macht das Verzeichnis 'api' zu einem Python-Paket und
                exportiert die wichtigsten Module und Funktionen.
 Autor:         Network Dashboard Team
 Erstellt:      2026-04-10
 Version:       1.0.0
================================================================================
"""

# Import der API-Module für einfacheren Zugriff
from api.routes import api_blueprint
from api.services import NetworkService, SystemService

# Paket-Metadaten
__version__ = '1.0.0'
__author__ = 'Network Dashboard Team'

# Öffentliche API-Exporte
__all__ = [
    'api_blueprint',
    'NetworkService',
    'SystemService',
]
