/**
 * ==============================================================================
 * BENACHRICHTIGUNGEN - Network Operations Dashboard
 * ==============================================================================
 * Datei:         static/js/notifications.js
 * Beschreibung:  Verwaltet Toast-Benachrichtigungen und das Event-Log in der
 *                rechten Sidebar. Zentrale Schnittstelle für User-Feedback.
 * Autor:         Network Dashboard Team
 * Erstellt:      2026-04-10
 * Version:       1.0.0
 * ==============================================================================
 */

class NotificationManager {
    constructor() {
        this.container = document.getElementById('notification-container');
        this.logContainer = document.getElementById('log-container');
        this.maxLogEntries = 100;
        
        this._bindEvents();
    }

    /**
     * Bindet notwendige Event-Listener
     */
    _bindEvents() {
        const clearBtn = document.getElementById('btn-clear-log');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearLog());
        }
    }

    /**
     * Zeigt eine Toast-Benachrichtigung an
     * @param {string} title - Der Titel der Benachrichtigung
     * @param {string} message - Die detaillierte Nachricht
     * @param {string} type - Typ ('success', 'error', 'warning', 'info')
     * @param {number} duration - Anzeigedauer in ms (0 = bleibt bis Klick)
     */
    show(title, message, type = 'info', duration = 5000) {
        if (!this.container) return;

        // Icons basierend auf Typ
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle',
            'ping': 'fa-satellite-dish'
        };

        const iconClass = icons[type] || icons['info'];
        
        // Element erstellen
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas ${iconClass}"></i>
            </div>
            <div class="notification-body">
                <h4 class="notification-title">${title}</h4>
                <p class="notification-message">${message}</p>
            </div>
            <button class="notification-close" aria-label="Schließen">
                <i class="fas fa-times"></i>
            </button>
        `;

        // In den Container einfügen
        this.container.appendChild(notification);

        // Klick auf Schließen
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => this._removeNotification(notification));

        // Automatisch schließen nach duration
        if (duration > 0) {
            // Fortschrittsbalken hinzufügen
            const progress = document.createElement('div');
            progress.className = 'notification-progress';
            progress.style.transitionDuration = `${duration}ms`;
            notification.appendChild(progress);
            
            // Animation für Fortschrittsbalken starten
            setTimeout(() => {
                progress.style.width = '100%';
            }, 10);

            // Timer für Entfernung
            setTimeout(() => {
                if (notification.parentNode) {
                    this._removeNotification(notification);
                }
            }, duration);
        }
    }

    /**
     * Entfernt eine Benachrichtigung mit Animation
     * @param {HTMLElement} notification - Das zu entfernende Element
     */
    _removeNotification(notification) {
        notification.classList.add('removing');
        notification.addEventListener('animationend', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    /**
     * Fügt einen Eintrag zum Aktivitäts-Log (Sidebar) hinzu
     * @param {string} message - Die Nachricht
     * @param {string} type - Typ ('success', 'error', 'warning', 'info', 'ping')
     */
    log(message, type = 'info') {
        if (!this.logContainer) return;

        // Icons basierend auf Typ
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-times-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle',
            'ping': 'fa-satellite-dish'
        };

        const iconClass = icons[type] || icons['info'];
        const timeStr = window.Utils ? window.Utils.formatTimeOnly(new Date()) : new Date().toLocaleTimeString();

        // Element erstellen
        const entry = document.createElement('div');
        entry.className = `log-entry log-entry-${type}`;
        
        entry.innerHTML = `
            <span class="log-time">${timeStr}</span>
            <span class="log-icon"><i class="fas ${iconClass}"></i></span>
            <span class="log-message">${message}</span>
        `;

        // Als erstes Element einfügen (neuestes oben)
        this.logContainer.insertBefore(entry, this.logContainer.firstChild);

        // Maximale Anzahl Einträge prüfen und ggf. älteste löschen
        while (this.logContainer.children.length > this.maxLogEntries) {
            this.logContainer.removeChild(this.logContainer.lastChild);
        }
    }

    /**
     * Leert das gesamte Aktivitäts-Log
     */
    clearLog() {
        if (!this.logContainer) return;
        
        // Letzten System-Meldung beibehalten (Dass das Log geleert wurde)
        this.logContainer.innerHTML = '';
        this.log('Aktivitäts-Log wurde manuell geleert.', 'info');
    }

    // Helper-Methoden für verschiedene Typen
    success(title, message, duration = 5000) {
        this.show(title, message, 'success', duration);
    }

    error(title, message, duration = 8000) {
        this.show(title, message, 'error', duration);
    }

    warning(title, message, duration = 6000) {
        this.show(title, message, 'warning', duration);
    }

    info(title, message, duration = 5000) {
        this.show(title, message, 'info', duration);
    }
}

// Singleton-Instanz erstellen
window.Notifications = new NotificationManager();
