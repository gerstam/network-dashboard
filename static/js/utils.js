/**
 * ==============================================================================
 * UTILITIES - Network Operations Dashboard
 * ==============================================================================
 * Datei:         static/js/utils.js
 * Beschreibung:  Sammlung von Hilfsfunktionen für Formatierungen,
 *                DOM-Manipulationen, Zeitberechnungen und mehr.
 * Autor:         Network Dashboard Team
 * Erstellt:      2026-04-10
 * Version:       1.0.0
 * ==============================================================================
 */

const Utils = {
    /**
     * Formatiert eine Zahl mit Trennzeichen (z.B. 1.000.000)
     * @param {number} num - Die zu formatierende Zahl
     * @returns {string} Die formatierte Zahl als String
     */
    formatNumber(num) {
        if (num === null || num === undefined) return '--';
        return new Intl.NumberFormat('de-DE').format(num);
    },

    /**
     * Formatiert Bytes in eine lesbare Größe (KB, MB, GB, etc.)
     * @param {number} bytes - Größe in Bytes
     * @param {number} decimals - Anzahl der Nachkommastellen
     * @returns {string} Formatierte Größe mit Einheit
     */
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0 || bytes === undefined || bytes === null) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },

    /**
     * Formatiert einen Prozentwert
     * @param {number} value - Der Prozentwert (0-100)
     * @param {number} decimals - Anzahl der Nachkommastellen
     * @returns {string} Formatierter Prozentwert mit %
     */
    formatPercent(value, decimals = 1) {
        if (value === null || value === undefined) return '--%';
        return parseFloat(value).toFixed(decimals) + '%';
    },

    /**
     * Aktualisiert die aktuelle Uhrzeit in den angegebenen DOM-Elementen
     * @param {string} timeId - ID des Elements für die Uhrzeit
     * @param {string} dateId - ID des Elements für das Datum
     */
    updateClock(timeId, dateId) {
        const timeEl = document.getElementById(timeId);
        const dateEl = document.getElementById(dateId);
        
        if (!timeEl && !dateEl) return;
        
        const now = new Date();
        
        if (timeEl) {
            timeEl.textContent = now.toLocaleTimeString('de-DE', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
        
        if (dateEl) {
            dateEl.textContent = now.toLocaleDateString('de-DE', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        }
    },

    /**
     * Erzeugt eine kleine Verzögerung (hilfreich für async/await)
     * @param {number} ms - Dauer in Millisekunden
     * @returns {Promise} Promise, das nach ms auflöst
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * Bestimmt die Status-Klasse basierend auf einem Prozentwert (z.B. für CPU/RAM)
     * @param {number} value - Der Wert in Prozent
     * @param {number} warningThreshold - Warnungs-Schwellenwert
     * @param {number} criticalThreshold - Kritischer Schwellenwert
     * @returns {string} 'normal', 'warning' oder 'critical'
     */
    getStatusClass(value, warningThreshold = 70, criticalThreshold = 90) {
        if (value >= criticalThreshold) return 'critical';
        if (value >= warningThreshold) return 'warning';
        return 'normal';
    },

    /**
     * Überprüft, ob ein Element im Viewport sichtbar ist
     * @param {HTMLElement} el - Das zu prüfende Element
     * @returns {boolean} true, wenn sichtbar
     */
    isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    },

    /**
     * Entprellt (debounces) eine Funktion, um sie nicht zu oft auszuführen
     * @param {Function} func - Die zu entprellende Funktion
     * @param {number} wait - Wartezeit in ms
     * @returns {Function} Entprellte Funktion
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
     /**
     * Formatiert ein ISO-Datum in eine lesbare Uhrzeit
     * @param {string} isoString - ISO-Datumsstring
     * @returns {string} Formatierte Uhrzeit (HH:MM:SS)
     */
    formatTimeOnly(isoString) {
        if (!isoString) return '--:--:--';
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString('de-DE', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (e) {
            return '--:--:--';
        }
    }
};

window.Utils = Utils;
