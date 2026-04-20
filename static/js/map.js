/**
 * ==============================================================================
 * KARTEN-LOGIK - Network Operations Dashboard
 * ==============================================================================
 * Datei:         static/js/map.js
 * Beschreibung:  Initialisiert und steuert die Leaflet-Karte. Verarbeitet
 *                Standortdaten, erzeugt benutzerdefinierte Marker und
 *                bindet Popups an die Marker.
 * Autor:         Network Dashboard Team
 * Erstellt:      2026-04-10
 * Version:       1.0.0
 * ==============================================================================
 */

class DashboardMap {
    constructor(containerId) {
        this.containerId = containerId;
        this.map = null;
        this.markers = {};
        this.config = null;
        this.locations = null;
        this.connectionLine = null;
    }

    /**
     * Initialisiert die Karte mit Konfigurationsdaten vom Server
     * @param {Object} config - Die API config/locations Daten
     */
    init(configData) {
        if (this.map) return; // Bereits initialisiert

        this.config = configData.map;
        this.locations = configData.locations;

        // Leaflet-Karte erstellen
        this.map = L.map(this.containerId, {
            center: this.config.center || [49.1596, 12.4279],
            zoom: this.config.zoom || 6,
            minZoom: this.config.min_zoom || 3,
            maxZoom: this.config.max_zoom || 18,
            zoomControl: false, // Wir fügen unsere eigene Kontrolle hinzu
            attributionControl: false // Wir fügen unsere eigene hinzu
        });

        // Dark-Theme Tile-Layer hinzufügen (CartoDB Dark Matter)
        const tileUrl = this.config.tile_url || 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
        const attribution = this.config.tile_attribution || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

        L.tileLayer(tileUrl, {
            attribution: attribution,
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.map);

        // Zoom-Kontrolle an benutzerdefinierter Position
        L.control.zoom({ position: 'topright' }).addTo(this.map);
        
        // Attribution an benutzerdefinierter Position
        L.control.attribution({ position: 'bottomright' }).addTo(this.map);

        // Marker und Verbindungen rendern
        this._renderMarkers();
        this._renderConnections();
        this._bindEvents();

        // Initiale Anpassung des Views, um alle Marker zu zeigen
        this.fitBounds();
    }

    /**
     * Bindet UI-Events der Karte
     */
    _bindEvents() {
        // Toolbar Buttons
        const btnFit = document.getElementById('btn-map-fit');
        const btnFfm = document.getElementById('btn-map-frankfurt');
        const btnVie = document.getElementById('btn-map-wien');

        if (btnFit) btnFit.addEventListener('click', () => this.fitBounds());
        
        if (btnFfm) {
            btnFfm.addEventListener('click', () => {
                this.flyToLocation('frankfurt');
                btnFfm.classList.add('animate-pulse');
                setTimeout(() => btnFfm.classList.remove('animate-pulse'), 1000);
            });
        }
        
        if (btnVie) {
            btnVie.addEventListener('click', () => {
                this.flyToLocation('wien');
                btnVie.classList.add('animate-shake');
                setTimeout(() => btnVie.classList.remove('animate-shake'), 500);
            });
        }

        // Global Event Listener für Popups öffnen
        document.addEventListener('openLocationDetail', (e) => {
            const locId = e.detail;
            const openModalBtn = document.getElementById(`btn-detail-${locId}`);
            if (openModalBtn) {
                openModalBtn.click();
            } else if (window.App && window.App.showLocationModal) {
                // Fallback, wenn der Button noch nicht im DOM ist (weil Popup geschlossen)
                window.App.showLocationModal(locId);
            }
        });
    }

    /**
     * Erstellt den HTML-Code für Custom Marker Icons
     * @param {Object} location - Standortdaten
     * @returns {string} HTML String für das Marker DivIcon
     */
    _createMarkerHTML(location) {
        const isOnline = location.status === 'online';
        const statusClass = isOnline ? 'marker-online' : 'marker-offline';
        const iconClass = location.icon || (isOnline ? 'fa-server' : 'fa-building');
        
        let glowHtml = '';
        if (location.marker_glow && isOnline) {
            glowHtml = `
                <div class="marker-glow">
                    <div class="marker-glow-core"></div>
                    <div class="marker-glow-ring marker-glow-ring-1"></div>
                    <div class="marker-glow-ring marker-glow-ring-2"></div>
                    <div class="marker-glow-ring marker-glow-ring-3"></div>
                </div>
            `;
        }

        return `
            <div class="custom-marker ${statusClass}" title="${location.name} (${isOnline ? 'Online' : 'Offline'})">
                ${glowHtml}
                <div class="marker-pin">
                    <div class="marker-status-dot"></div>
                    <i class="fas ${iconClass} marker-icon"></i>
                </div>
                <div class="marker-label">${location.short_name}</div>
            </div>
        `;
    }

    /**
     * Setzt Marker für alle konfigurierten Standorte auf der Karte
     */
    _renderMarkers() {
        if (!this.locations) return;

        for (const [id, loc] of Object.entries(this.locations)) {
            // Leaflet Custom DivIcon erstellen
            const customIcon = L.divIcon({
                className: 'transparent-marker', // Wir setzen das Styling im HTML
                html: this._createMarkerHTML(loc),
                iconSize: [40, 40],
                iconAnchor: [20, 20],
                popupAnchor: [0, -25]
            });

            // Marker erstellen und zur Karte hinzufügen
            const marker = L.marker([loc.latitude, loc.longitude], {
                icon: customIcon,
                title: loc.name,
                zIndexOffset: loc.status === 'online' ? 1000 : 0 // Online Marker nach vorne
            }).addTo(this.map);

            // Initiale Popup-Struktur (wird später von _updatePopupContent aktualisiert)
            marker.bindPopup("<div class='sysinfo-loading'><div class='spinner'></div></div>", {
                maxWidth: 320,
                minWidth: 260,
                className: 'custom-dashboard-popup'
            });

            // Event-Listener: Beim Öffnen des Popups die aktuellen Daten rendern
            marker.on('popupopen', () => this._updatePopupContent(id, marker));

            // Marker in der Instanz speichern für späteren Zugriff
            this.markers[id] = marker;
        }
    }

    /**
     * Erzeugt eine visuelle Verbindungslinie zwischen den Standorten
     */
    _renderConnections() {
        // Brauchen mindestens Frankfurt und Wien
        if (!this.locations.frankfurt || !this.locations.wien) return;

        const ffm = [this.locations.frankfurt.latitude, this.locations.frankfurt.longitude];
        const vie = [this.locations.wien.latitude, this.locations.wien.longitude];

        // Die Linie wird gestrichelt dargestellt, basierend auf CSS .leaflet-connection-line
        this.connectionLine = L.polyline([ffm, vie], {
            className: 'leaflet-connection-line animated-dash',
            dashArray: '8, 8',
            dashOffset: '0'
        }).addTo(this.map);
    }

    /**
     * Aktualisiert den Inhalt eines Popups mit Echtzeit-Daten
     * @param {string} locationId - ID des Standorts
     * @param {L.Marker} marker - Referenz auf den Leaflet Marker
     */
    _updatePopupContent(locationId, marker) {
        // Falls wir Daten im globalen App-Zustand haben, nutzen wir diese
        // ansonsten nutzen wir die initiale Konfiguration (weniger aktuell)
        let data = this.locations[locationId];
        
        if (window.App && window.App.state && window.App.state.statusData) {
            const locData = window.App.state.statusData.locations;
            if (locData && locData[locationId]) {
                data = locData[locationId];
            }
        }

        const isOnline = data.status === 'online';
        const statusText = isOnline ? 'ONLINE' : 'OFFLINE';
        const iconClass = isOnline ? 'fa-server' : 'fa-building';
        const statusIconClass = isOnline ? 'online' : 'offline';
        
        let uptimeHtml = '';
        if (isOnline && data.uptime) {
            uptimeHtml = `<div class="popup-info-value font-mono">${data.uptime.formatted}</div>`;
        } else {
            uptimeHtml = `<div class="popup-info-value">Nicht verfügbar</div>`;
        }

        const html = `
            <div class="popup-content">
                <div class="popup-header">
                    <div class="popup-status-icon ${statusIconClass}">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="popup-title-section">
                        <h4 class="popup-title">${data.name}</h4>
                        <p class="popup-subtitle">${data.datacenter} | ${data.team}</p>
                    </div>
                </div>
                <div class="popup-body">
                    <div class="popup-info-grid">
                        <div class="popup-info-item">
                            <span class="popup-info-label">Status</span>
                            <span class="popup-info-value font-bold ${isOnline ? 'text-online' : 'text-offline'}">${statusText}</span>
                        </div>
                        <div class="popup-info-item">
                            <span class="popup-info-label">IP Adresse</span>
                            <span class="popup-info-value font-mono">${data.ip_address}</span>
                        </div>
                        <div class="popup-info-item">
                            <span class="popup-info-label">Betriebszeit</span>
                            ${uptimeHtml}
                        </div>
                    </div>
                </div>
                <div class="popup-footer">
                    <button class="popup-btn btn-popup-ping" onclick="document.dispatchEvent(new CustomEvent('pingLocation', {detail: '${locationId}'})); this.closest('.leaflet-popup').remove();">
                        <i class="fas fa-satellite-dish"></i> Ping
                    </button>
                    <button class="popup-btn btn-popup-detail" id="btn-detail-${locationId}" onclick="document.dispatchEvent(new CustomEvent('openLocationDetail', {detail: '${locationId}'})); this.closest('.leaflet-popup').remove();">
                        <i class="fas fa-list-ul"></i> Details
                    </button>
                </div>
            </div>
        `;

        marker.setPopupContent(html);
    }

    /**
     * Aktualisiert das visuelle Erscheinungsbild aller Marker
     * (z.B. nach einem Status-Update)
     * @param {Object} statusData - Aktuelle Statusdaten der API
     */
    updateMarkers(statusData) {
        if (!statusData || !statusData.locations) return;

        for (const [id, data] of Object.entries(statusData.locations)) {
            const marker = this.markers[id];
            if (!marker) continue;

            const wasOnline = marker.options.zIndexOffset === 1000;
            const isOnline = data.status === 'online';

            // Nur updaten, wenn sich der Status geändert hat
            if (wasOnline !== isOnline) {
                // Neues Icon generieren
                const customIcon = L.divIcon({
                    className: 'transparent-marker',
                    html: this._createMarkerHTML(data),
                    iconSize: [40, 40],
                    iconAnchor: [20, 20],
                    popupAnchor: [0, -25]
                });

                marker.setIcon(customIcon);
                marker.setZIndexOffset(isOnline ? 1000 : 0);
            }
        }
    }

    /**
     * Fokussiert die Karte so, dass alle Marker sichtbar sind
     */
    fitBounds() {
        if (!this.map || Object.keys(this.markers).length === 0) return;

        const bounds = L.latLngBounds();
        for (const marker of Object.values(this.markers)) {
            bounds.extend(marker.getLatLng());
        }

        this.map.flyToBounds(bounds, {
            padding: [50, 50],
            duration: 1.5,
            easeLinearity: 0.25
        });
    }

    /**
     * Fliegt zu einem bestimmten Standort
     * @param {string} locationId - ID des Standorts
     */
    flyToLocation(locationId) {
        if (!this.map || !this.markers[locationId]) return;

        const marker = this.markers[locationId];
        
        this.map.flyTo(marker.getLatLng(), 8, {
            duration: 1.5,
            easeLinearity: 0.25
        });

        // Warten bis Animation fertig, dann Popup öffnen
        this.map.once('moveend', () => {
            marker.openPopup();
        });
    }
}
