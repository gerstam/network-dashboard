/**
 * ==============================================================================
 * API CLIENT - Network Operations Dashboard
 * ==============================================================================
 * Datei:         static/js/api.js
 * Beschreibung:  Zentraler API-Client für die Kommunikation mit dem Backend.
 *                Kapselt alle Fetch-Aufrufe, Fehlerbehandlung und Timeouts.
 * Autor:         Network Dashboard Team
 * Erstellt:      2026-04-10
 * Version:       1.0.0
 * ==============================================================================
 */

class ApiClient {
    constructor() {
        this.baseUrl = '/api';
        this.defaultTimeout = 10000; // 10 Sekunden
    }

    /**
     * Zentrale Fetch-Methode mit Timeout- und Fehlerbehandlung
     * @param {string} endpoint - Der API-Endpunkt (z.B. '/status')
     * @param {Object} options - Fetch Options
     * @returns {Promise<any>} API-Antwortdaten
     */
    async _fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        // Timeout-Controller einrichten
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.defaultTimeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                const errorMessage = data.error || `HTTP Error: ${response.status}`;
                throw new Error(errorMessage);
            }
            
            return data.data;
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                console.error(`API Timeout bei Anfrage an ${url}`);
                throw new Error('Zeitüberschreitung bei der Server-Anfrage.');
            }
            
            console.error(`API Fehler bei Anfrage an ${url}:`, error);
            throw error;
        }
    }

    /**
     * Holt die Dashboard-Konfiguration
     * @returns {Promise<Object>} Dashboard config
     */
    async getDashboardConfig() {
        return this._fetch('/config/dashboard');
    }

    /**
     * Holt die Standort-Konfigurationen für die Karte
     * @returns {Promise<Object>} Locations config
     */
    async getLocationsConfig() {
        return this._fetch('/config/locations');
    }

    /**
     * Holt den Status aller oder eines bestimmten Standorts
     * @param {string} locationId - (Optional) Bestimmter Standort
     * @returns {Promise<Object>} Status-Daten
     */
    async getStatus(locationId = null) {
        const endpoint = locationId ? `/status?location=${locationId}` : '/status';
        return this._fetch(endpoint);
    }

    /**
     * Führt einen Ping zu einem Standort aus
     * @param {string} locationId - ID des Standorts ('frankfurt', 'wien')
     * @returns {Promise<Object>} Ping-Ergebnisse
     */
    async pingLocation(locationId) {
        // Ping kann länger dauern, daher höheres Timeout (z.B. 15s)
        return this._fetch(`/ping/${locationId}`, { timeout: 15000 });
    }

    /**
     * Holt den Ping-Verlauf eines Standorts
     * @param {string} locationId - ID des Standorts
     * @param {number} limit - Anzahl der Einträge
     * @returns {Promise<Object>} Ping-Historie
     */
    async getPingHistory(locationId, limit = 20) {
        return this._fetch(`/ping/${locationId}/history?limit=${limit}`);
    }

    /**
     * Holt umfassende Systeminformationen
     * @param {string} section - (Optional) Bestimmte Sektion
     * @returns {Promise<Object>} Systeminformationen
     */
    async getSystemInfo(section = null) {
        const endpoint = section ? `/systeminfo?section=${section}` : '/systeminfo';
        // System-Abfrage kann dauern, wenn keine Caches vorhanden sind
        return this._fetch(endpoint, { timeout: 15000 });
    }

    /**
     * Holt den System-Health-Status
     * @returns {Promise<Object>} Health Status (nicht die kompletten Sysinfos)
     */
    async getSystemHealth() {
        return this._fetch('/systeminfo/health');
    }
}

// Singleton-Instanz erstellen
window.API = new ApiClient();
