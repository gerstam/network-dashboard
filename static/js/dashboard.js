/**
 * ==============================================================================
 * DASHBOARD UI LOGIK - Network Operations Dashboard
 * ==============================================================================
 * Datei:         static/js/dashboard.js
 * Beschreibung:  Aktualisiert die DOM-Elemente des Dashboards (Status-Karten,
 *                Navbar-Badges, System-Metriken etc.) basierend auf den
 *                Daten vom Backend.
 * Autor:         Network Dashboard Team
 * Erstellt:      2026-04-10
 * Version:       1.0.0
 * ==============================================================================
 */

class DashboardUI {
    constructor() {
        this._bindModals();
    }

    /**
     * Bindet die Event-Listener für die Modal-Dialoge
     */
    _bindModals() {
        // Modal Overlay Klick (Alle schließen)
        const overlay = document.getElementById('modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => this.closeAllModals());
        }

        // Close Buttons für jedes Modal
        document.querySelectorAll('.modal-close, .modal-footer .btn-primary').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    /**
     * Aktualisiert die Navbar basierend auf Statusdaten
     * @param {Object} statusData - Daten vom /api/status Endpunkt
     */
    updateNavbar(statusData) {
        if (!statusData || !statusData.locations) return;

        for (const [id, data] of Object.entries(statusData.locations)) {
            const badge = document.getElementById(`navbar-badge-${id}`);
            if (!badge) continue;

            const isOnline = data.status === 'online';
            
            // Klassen aktualisieren
            badge.className = `status-badge ${isOnline ? 'status-badge-online' : 'status-badge-offline'}`;
            
            // Icon-Container (Punkt)
            const dot = badge.querySelector('.badge-dot');
            if (dot) {
                dot.className = `badge-dot ${isOnline ? 'badge-dot-online' : 'badge-dot-offline'}`;
                
                // Puls-Effekt für Online-Status
                if (isOnline) {
                    if (!dot.querySelector('.badge-dot-pulse')) {
                        dot.innerHTML = '<span class="badge-dot-pulse"></span>';
                    }
                } else {
                    dot.innerHTML = '';
                }
            }

            // Statustext
            const statusSpan = badge.querySelector('.badge-status');
            if (statusSpan) {
                statusSpan.textContent = isOnline ? 'ONLINE' : 'OFFLINE';
            }
            
            // Tooltip
            badge.setAttribute('title', `${data.short_name} - ${isOnline ? 'Online' : 'Offline'}`);
        }
    }

    /**
     * Aktualisiert die Gesundheits-Gauge und Zusammenfassung
     * @param {Object} summaryData - Zusammenfassungsdaten (online/offline count)
     */
    updateHealthWidget(summaryData) {
        if (!summaryData) return;

        // Prozentwert
        const gaugeValue = document.getElementById('gauge-value');
        const gaugeProgress = document.getElementById('gauge-progress');
        const healthBadge = document.getElementById('health-badge');

        if (gaugeValue) gaugeValue.textContent = Math.round(summaryData.health_percentage);
        
        if (gaugeProgress) {
            // Kreisumfang (stroke-dasharray="326.73")
            const circumference = 326.73;
            // Prozentbereich in Offset umrechnen (100% = 0, 0% = 326.73)
            const offset = circumference - (summaryData.health_percentage / 100) * circumference;
            gaugeProgress.style.strokeDashoffset = offset;

            // Farbe anpassen
            let color = 'var(--color-online)'; // Default grün
            if (summaryData.health_percentage < 50) color = 'var(--color-offline)'; // Rot
            else if (summaryData.health_percentage < 100) color = 'var(--color-warning)'; // Orange

            gaugeProgress.style.stroke = color;
            gaugeValue.parentElement.style.color = color;
            
            if (healthBadge) {
                healthBadge.style.background = `rgba(${this._hexToRgb(color)}, 0.15)`;
                healthBadge.style.color = color;
                healthBadge.style.borderColor = `rgba(${this._hexToRgb(color)}, 0.3)`;
                
                if (summaryData.health_percentage === 100) healthBadge.textContent = 'OK';
                else if (summaryData.health_percentage >= 50) healthBadge.textContent = 'WARNUNG';
                else healthBadge.textContent = 'KRITISCH';
            }
        }

        // Zähler
        const onlineCount = document.getElementById('stat-online-count');
        const offlineCount = document.getElementById('stat-offline-count');
        const totalCount = document.getElementById('stat-total-count');

        if (onlineCount) onlineCount.textContent = summaryData.online;
        if (offlineCount) offlineCount.textContent = summaryData.offline;
        if (totalCount) totalCount.textContent = summaryData.total;
    }

    /**
     * Aktualisiert eine Standort-Karte in der Sidebar
     * @param {string} id - Standort-ID
     * @param {Object} data - Standortdaten
     */
    updateLocationCard(id, data) {
        const card = document.getElementById(`card-${id}`);
        if (!card) return;

        const isOnline = data.status === 'online';

        // Karte Styling
        card.className = `dashboard-card card-location ${isOnline ? 'card-online hover-lift' : 'card-offline'}`;

        // Header Icon
        const icon = card.querySelector('.card-icon');
        if (icon) {
            icon.className = `fas ${isOnline ? 'fa-server' : 'fa-building'} card-icon ${isOnline ? 'card-icon-online' : 'card-icon-offline'}`;
        }

        // Status Indikator
        const indicator = document.getElementById(`status-indicator-${id}`);
        if (indicator) {
            indicator.className = `status-indicator ${isOnline ? 'status-online' : 'status-offline'}`;
            indicator.innerHTML = isOnline ? '<span class="status-pulse"></span> ONLINE' : 'OFFLINE';
        }

        // Animation für Update (kurzes Aufleuchten)
        card.classList.add('data-updated');
        setTimeout(() => card.classList.remove('data-updated'), 1000);

        // Uptime rendern
        const uptimeEl = document.getElementById(`${id}-uptime`);
        if (uptimeEl) {
            if (isOnline && data.uptime) {
                uptimeEl.textContent = data.uptime.formatted;
                uptimeEl.className = 'info-value font-mono text-online';
            } else {
                uptimeEl.textContent = 'Nicht verfügbar';
                uptimeEl.className = 'info-value text-muted';
            }
        }

        // Latenz rendern
        const latencyEl = document.getElementById(`${id}-latency`);
        if (latencyEl) {
            if (data.last_ping) {
                if (data.last_ping.status === 'success') {
                    latencyEl.textContent = `${data.last_ping.avg_ms} ms`;
                    let colorClass = 'text-online';
                    // Schwellenwerte für Latenzfarben
                    if (data.last_ping.avg_ms > 100) colorClass = 'text-warning';
                    if (data.last_ping.avg_ms > 500) colorClass = 'text-offline';
                    latencyEl.className = `info-value font-mono ${colorClass}`;
                } else {
                    latencyEl.textContent = 'Timeout';
                    latencyEl.className = 'info-value font-mono text-offline';
                }
            } else {
                latencyEl.textContent = '-- ms';
            }
        }

        // Services-Dots aktualisieren
        const servicesContainer = document.getElementById(`${id}-services`);
        if (servicesContainer && data.services) {
            const dotsContainer = servicesContainer.querySelector('.services-dots');
            const countEl = servicesContainer.querySelector('.services-count');
            
            if (dotsContainer && countEl) {
                let html = '';
                let runningCount = 0;
                
                data.services.forEach(service => {
                    const isRunning = service.status === 'running';
                    if (isRunning) runningCount++;
                    html += `<span class="service-dot ${isRunning ? 'online' : 'offline'}" title="${service.name}"></span>`;
                });
                
                dotsContainer.innerHTML = html;
                countEl.textContent = `${runningCount}/${data.services.length}`;
            }
        }
    }

    /**
     * Aktualisiert das System-Health Widget (rechte Sidebar)
     * @param {Object} healthData - Gesundheitsdaten vom /api/systeminfo/health
     */
    updateSystemHealthWidget(healthData) {
        if (!healthData || !healthData.checks) return;

        const metrics = ['cpu', 'memory', 'disk'];
        const idMap = { 'cpu': 'cpu', 'memory': 'ram', 'disk': 'disk' };

        metrics.forEach(metric => {
            const domId = idMap[metric];
            const data = healthData.checks[metric];
            if (!data) return;

            // Value
            const valueEl = document.getElementById(`metric-${domId}-value`);
            if (valueEl) valueEl.textContent = `${data.value.toFixed(1)}${data.unit}`;

            // Bar
            const barEl = document.getElementById(`metric-${domId}-bar`);
            if (barEl) {
                barEl.style.width = `${data.value}%`;
                
                // Color based on status
                if (data.status === 'critical') {
                    barEl.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
                    if (valueEl) valueEl.className = 'metric-value text-offline';
                } else if (data.status === 'warning') {
                    barEl.style.background = 'linear-gradient(90deg, var(--color-warning), #ea580c)';
                    if (valueEl) valueEl.className = 'metric-value text-warning';
                } else {
                    barEl.style.background = 'linear-gradient(90deg, var(--color-accent-primary), var(--color-online))';
                    if (valueEl) valueEl.className = 'metric-value text-online';
                }
            }
        });
    }

    /**
     * Rendert die Ping-Historie als simple Balken im Ping-Modal
     * @param {Array} latencies - Array von Latenzen
     * @param {HTMLElement} container - DOM Element
     */
    renderPingLatencies(latencies, container) {
        if (!container || !latencies || latencies.length === 0) {
            if(container) container.innerHTML = '<p class="text-muted text-sm italic">Keine Latenzdaten verfügbar</p>';
            return;
        }

        const count = latencies.length;
        const max = Math.max(...latencies) * 1.2; // 20% Puffer oben
        
        let html = '';
        latencies.forEach((val, i) => {
            const pct = max > 0 ? (val / max) * 100 : 0;
            // Farbige Balken (kurz = grün, lang = rot)
            let color = 'linear-gradient(90deg, var(--color-accent-primary), var(--color-online))';
            if (val > 100) color = 'linear-gradient(90deg, var(--color-warning), #ea580c)';
            if (val > 300) color = 'linear-gradient(90deg, #ef4444, #dc2626)';

            html += `
                <div class="ping-latency-item animate-fade-in-right" style="animation-delay: ${i * 0.1}s">
                    <span class="ping-latency-label">Seq ${i+1}</span>
                    <div class="ping-latency-bar-wrapper">
                        <div class="ping-latency-bar" style="width: ${pct}%; background: ${color}"></div>
                    </div>
                    <span class="ping-latency-value">${val} ms</span>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    // --- Modal Management ---

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        const overlay = document.getElementById('modal-overlay');
        
        if (modal && overlay) {
            overlay.classList.add('active');
            modal.classList.add('active');
            // Fokus in Modal setzen für A11y (vereinfacht)
            const focusable = modal.querySelector('button');
            if (focusable) focusable.focus();
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.remove('active');
        
        // Overlay nur ausblenden, wenn keine anderen Modals aktiv sind
        const activeModals = document.querySelectorAll('.modal.active');
        if (activeModals.length === 0) {
            const overlay = document.getElementById('modal-overlay');
            if (overlay) overlay.classList.remove('active');
        }
    }

    closeAllModals() {
        document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
        const overlay = document.getElementById('modal-overlay');
        if (overlay) overlay.classList.remove('active');
    }

    // Internes Helferlein für rgba
    _hexToRgb(hex) {
        // Simple regex für hex zu rbg conversion
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if(result) {
            return `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`;
        }
        
        // Fallback IDs für CSS Variablen Name mapping (dirty but works for predefined vars here)
        if(hex.includes('online')) return '0, 255, 136';
        if(hex.includes('offline')) return '255, 68, 85';
        if(hex.includes('warning')) return '245, 158, 11';
        
        return '255, 255, 255';
    }
}

// Singleton
window.DashboardUI = new DashboardUI();
