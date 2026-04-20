/**
 * ==============================================================================
 * CENTRAL APPLICATION LOGIC - Network Operations Dashboard
 * ==============================================================================
 * Datei:         static/js/app.js
 * Beschreibung:  Haupt-Einstiegspunkt für die Frontend-Logik. Initialisiert
 *                die Anwendung, steuert den globalen Zustand, startet die
 *                Auto-Refresh-Zyklen und verbindet UI-Events mit API-Aufrufen.
 * Autor:         Network Dashboard Team
 * Erstellt:      2026-04-10
 * Version:       1.0.0
 * ==============================================================================
 */

class Application {
    constructor() {
        this.api = window.API;
        this.ui = window.DashboardUI;
        this.notifications = window.Notifications;
        this.map = new DashboardMap('map');
        
        this.state = {
            config: null,
            statusData: null,
            autoRefresh: true,
            refreshInterval: 30000, // Fallback
            timers: {
                autoRefresh: null,
                clock: null,
                uptimeCounter: null,
                sysHealth: null
            },
            isInitialLoad: true
        };
    }

    /**
     * Startet die Anwendung
     */
    async init() {
        try {
            // 1. Uhren starten
            this._startClock();

            // 2. Basis-Konfiguration laden
            await this._loadConfig();

            // 3. Karte initialisieren
            this.map.init(this.state.config);

            // 4. Initialen Status laden
            await this.refreshStatus();

            // 5. System Health laden
            await this.refreshSystemHealth();

            // 6. UI-Interaktionen binden
            this._bindEvents();

            // 7. Auto-Refresh Intervalle starten
            this._startTimers();

            // 8. Ladebildschirm ausblenden
            this._hideLoadingScreen();

            this.notifications.log('Dashboard erfolgreich initialisiert.', 'success');
            
        } catch (error) {
            console.error('Kritischer Fehler bei der Initialisierung:', error);
            document.getElementById('loading-text').textContent = 'Fehler beim Starten. Bitte Seite neu laden.';
            document.getElementById('loading-text').style.color = 'var(--color-offline)';
            this.notifications.show('Initialisierungsfehler', error.message, 'error', 0); // Bleibt stehen
        }
    }

    /**
     * Lädt die Dashboard & Location config von der API
     */
    async _loadConfig() {
        const [dashConfig, locConfig] = await Promise.all([
            this.api.getDashboardConfig(),
            this.api.getLocationsConfig()
        ]);

        this.state.config = {
            ...dashConfig,
            ...locConfig
        };

        if (this.state.config.auto_refresh_interval) {
            this.state.refreshInterval = this.state.config.auto_refresh_interval * 1000;
        }
    }

    /**
     * Ruft den aktuellen Status aller Standorte ab
     */
    async refreshStatus() {
        try {
            const btn = document.getElementById('btn-refresh-status');
            if (btn) btn.classList.add('loading');

            // API Aufruf
            const statusData = await this.api.getStatus();
            this.state.statusData = statusData;

            // UI Aktualisieren
            this.ui.updateNavbar(statusData);
            this.ui.updateHealthWidget(statusData.summary);
            
            // Jede Location Card updaten
            for (const [id, data] of Object.entries(statusData.locations)) {
                this.ui.updateLocationCard(id, data);
            }

            // Karte aktualisieren
            this.map.updateMarkers(statusData);

            // Footer Timestamp
            const footerUpdate = document.getElementById('footer-last-update');
            if (footerUpdate) {
                footerUpdate.textContent = `Letztes Update: ${window.Utils.formatTimeOnly(statusData.last_update)}`;
            }

            if (!this.state.isInitialLoad) {
                this.notifications.log('Status manuell aktualisiert.', 'info');
            }
            this.state.isInitialLoad = false;

        } catch (error) {
            this.notifications.error('Status-Update fehlgeschlagen', error.message);
            
            const btn = document.getElementById('btn-refresh-status');
            if(btn) {
                btn.classList.add('animate-shake');
                setTimeout(() => btn.classList.remove('animate-shake'), 500);
            }

        } finally {
            const btn = document.getElementById('btn-refresh-status');
            if (btn) btn.classList.remove('loading');
        }
    }

    /**
     * Lädt das Local System Health Widget
     */
    async refreshSystemHealth() {
        try {
            const healthData = await this.api.getSystemHealth();
            this.ui.updateSystemHealthWidget(healthData);
            
            // Uptime auch grob setzen, wenn sysinfo endpunkt gebraucht wird später, dann dort holen
            const uptimeEl = document.getElementById('system-uptime-value');
            if (uptimeEl && healthData.timestamp) {
               // Wir zeigen hier simulativ "Lokal verbunden" 
               uptimeEl.innerHTML = '<span class="text-online">Online (Lokal)</span>';
            }

        } catch (error) {
            console.error('Fehler bei SystemHealth:', error);
        }
    }

    /**
     * Startet einen Ping-Vorgang zu einem Standort
     * @param {string} locationId - z.B. 'frankfurt' oder 'wien'
     */
    async executePing(locationId) {
        if (!this.state.config.locations[locationId]) return;

        const locName = this.state.config.locations[locationId].name;
        
        // Modal vorbereiten und öffnen
        const modalTitle = document.getElementById('modal-ping-title');
        const modalSub = document.getElementById('modal-ping-subtitle');
        const statusDisplay = document.getElementById('ping-status-display');
        const statsGrid = document.getElementById('ping-stats-grid');
        const latencyBars = document.getElementById('ping-latency-bars');
        const loadingDiv = document.getElementById('ping-loading');
        const contentDiv = document.getElementById('ping-result-content');
        const retryBtn = document.getElementById('btn-ping-retry');

        if (modalTitle) modalTitle.textContent = `Ping: ${locName}`;
        if (modalSub) modalSub.textContent = `Pinging ${this.state.config.locations[locationId].ip_address}...`;
        
        // Reset Modal State
        loadingDiv.style.display = 'flex';
        contentDiv.style.display = 'none';
        
        // WICHTIG: Event listener für retry button entfernen und neu setzen (um mehrfaches feuern zu vermeiden)
        const newRetryBtn = retryBtn.cloneNode(true);
        retryBtn.parentNode.replaceChild(newRetryBtn, retryBtn);
        newRetryBtn.addEventListener('click', () => this.executePing(locationId));

        this.ui.openModal('modal-ping');
        this.notifications.log(`Ping an ${locName} gesendet...`, 'ping');

        try {
            // API Aufruf
            // Künstliches Delay für UX (damit man die Ping animation sieht)
            const [pingResult] = await Promise.all([
                this.api.pingLocation(locationId),
                window.Utils.sleep(2000)
            ]);

            // Ergebnisse rendern
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';

            // 1. Status Badge
            const isSuccess = pingResult.status === 'success';
            let statusHtml = '';
            
            if (isSuccess) {
                statusHtml = `
                    <div class="ping-status-badge success animate-fade-in-up">
                        <i class="fas fa-check-circle"></i> Erfolgreich
                    </div>`;
                this.notifications.success('Ping Erfolgreich', `Latenz nach ${locName}: ${pingResult.avg_ms}ms`, 4000);
                this.notifications.log(`Ping ${locName}: Erfolgreich (${pingResult.avg_ms}ms)`, 'success');
            } else {
                const isTimeout = pingResult.status === 'timeout';
                const badgeClass = isTimeout ? 'timeout' : 'error';
                const icon = isTimeout ? 'fa-clock' : 'fa-exclamation-triangle';
                const text = isTimeout ? 'Zeitüberschreitung' : 'Fehler';
                
                statusHtml = `
                    <div class="ping-status-badge ${badgeClass} animate-fade-in-up">
                        <i class="fas ${icon}"></i> ${text}
                    </div>`;
                    
                this.notifications.warning('Ping Fehlgeschlagen', `Host ${locName} nicht erreichbar.`, 5000);
                this.notifications.log(`Ping ${locName}: ${text}`, 'error');
            }
            statusDisplay.innerHTML = statusHtml;

            // 2. Stats Grid
            statsGrid.innerHTML = `
                <div class="ping-stat animate-fade-in-up" style="animation-delay: 0.1s">
                    <div class="ping-stat-label">Gesendet / Empfangen</div>
                    <div class="ping-stat-value">${pingResult.packets_sent} / ${pingResult.packets_received}</div>
                </div>
                <div class="ping-stat animate-fade-in-up" style="animation-delay: 0.2s">
                    <div class="ping-stat-label">Paketverlust</div>
                    <div class="ping-stat-value ${pingResult.packet_loss > 0 ? 'text-offline' : ''}">${pingResult.packet_loss}<span class="ping-stat-unit">%</span></div>
                </div>
                <div class="ping-stat animate-fade-in-up" style="animation-delay: 0.3s">
                    <div class="ping-stat-label">Ø Latenz (Avg)</div>
                    <div class="ping-stat-value">${pingResult.avg_ms}<span class="ping-stat-unit">ms</span></div>
                </div>
                <div class="ping-stat animate-fade-in-up" style="animation-delay: 0.4s">
                    <div class="ping-stat-label">Min Latenz</div>
                    <div class="ping-stat-value">${pingResult.min_ms}<span class="ping-stat-unit">ms</span></div>
                </div>
                <div class="ping-stat animate-fade-in-up" style="animation-delay: 0.5s">
                    <div class="ping-stat-label">Max Latenz</div>
                    <div class="ping-stat-value">${pingResult.max_ms}<span class="ping-stat-unit">ms</span></div>
                </div>
                <div class="ping-stat animate-fade-in-up" style="animation-delay: 0.6s">
                    <div class="ping-stat-label">Jitter</div>
                    <div class="ping-stat-value">${pingResult.jitter_ms}<span class="ping-stat-unit">ms</span></div>
                </div>
            `;

            // 3. Latency Bars
            this.ui.renderPingLatencies(pingResult.latencies, latencyBars);

            // Letztendlich auch die Dashboard-Karte für diesen Standort mit updaten
            if(isSuccess) {
                this.refreshStatus(); // Aktualisiert alles, damit Historie / Frontend synchron bleiben
            }

        } catch (error) {
            loadingDiv.innerHTML = `<i class="fas fa-exclamation-triangle text-offline text-3xl mb-base"></i><p class="text-offline">API-Fehler: ${error.message}</p>`;
            this.notifications.error('Ping Error', error.message);
        }
    }

    /**
     * Holt ausführliche Systeminformationen und zeigt diese im Modal an
     */
    async showSystemInfo() {
        const loadingDiv = document.getElementById('sysinfo-loading');
        const contentDiv = document.getElementById('sysinfo-content');
        
        loadingDiv.style.display = 'flex';
        contentDiv.style.display = 'none';
        
        this.ui.openModal('modal-sysinfo');
        this.notifications.log('Systeminformationen angefordert...', 'info');

        try {
            const sysinfo = await this.api.getSystemInfo();
            
            // OS Section
            const osGrid = document.getElementById('sysinfo-os-grid');
            if (osGrid) {
                osGrid.innerHTML = `
                    <div class="sysinfo-item">
                        <span class="sysinfo-item-label">Plattform</span>
                        <span class="sysinfo-item-value">${sysinfo.os.system} ${sysinfo.os.release}</span>
                    </div>
                    <div class="sysinfo-item">
                        <span class="sysinfo-item-label">Architektur</span>
                        <span class="sysinfo-item-value">${sysinfo.os.architecture}</span>
                    </div>
                    <div class="sysinfo-item">
                        <span class="sysinfo-item-label">Hostname</span>
                        <span class="sysinfo-item-value">${sysinfo.os.node_name}</span>
                    </div>
                    <div class="sysinfo-item">
                        <span class="sysinfo-item-label">Python Version</span>
                        <span class="sysinfo-item-value">${sysinfo.python.version}</span>
                    </div>
                `;
            }

            // CPU Section
            const cpuOverview = document.getElementById('sysinfo-cpu-overview');
            const cpuCores = document.getElementById('sysinfo-cpu-cores');
            
            if (cpuOverview) {
                cpuOverview.innerHTML = `
                    <div class="sysinfo-big-bar">
                        <div class="sysinfo-big-bar-header">
                            <span class="sysinfo-big-bar-label">Gesamtauslastung ( ${sysinfo.cpu.logical_cores} Cores )</span>
                            <span class="sysinfo-big-bar-value ${sysinfo.cpu.status !== 'normal' ? 'text-' + sysinfo.cpu.status : ''}">${sysinfo.cpu.usage_percent.toFixed(1)}%</span>
                        </div>
                        <div class="sysinfo-bar-track">
                            <div class="sysinfo-bar-fill ${sysinfo.cpu.status}" style="width: ${sysinfo.cpu.usage_percent}%"></div>
                        </div>
                    </div>
                    <div class="sysinfo-detail-grid">
                        <div class="sysinfo-item">
                            <span class="sysinfo-item-label">Frequenz</span>
                            <span class="sysinfo-item-value">${sysinfo.cpu.frequency_mhz.current} MHz</span>
                        </div>
                        <div class="sysinfo-item">
                            <span class="sysinfo-item-label">Load Avg (1m 5m 15m)</span>
                            <span class="sysinfo-item-value">${sysinfo.cpu.load_average.join(' ')}</span>
                        </div>
                        <div class="sysinfo-item">
                            <span class="sysinfo-item-label">Protokoll</span>
                            <span class="sysinfo-item-value">${sysinfo.os.processor}</span>
                        </div>
                    </div>
                `;
            }

            if (cpuCores && sysinfo.cpu.usage_per_core) {
                let coresHtml = '';
                sysinfo.cpu.usage_per_core.forEach((core, i) => {
                    const statusClass = window.Utils.getStatusClass(core, 75, 90);
                    let grad = 'linear-gradient(90deg, var(--color-accent-primary), var(--color-online))';
                    if (statusClass === 'warning') grad = 'linear-gradient(90deg, var(--color-warning), #ea580c)';
                    if (statusClass === 'critical') grad = 'linear-gradient(90deg, #ef4444, #dc2626)';

                    coresHtml += `
                        <div class="sysinfo-core">
                            <div class="sysinfo-core-label">Core ${i}</div>
                            <div class="sysinfo-core-bar">
                                <div class="sysinfo-core-bar-fill" style="width: ${core}%; background: ${grad}"></div>
                            </div>
                            <div class="sysinfo-core-value ${statusClass !== 'normal' ? 'text-' + statusClass : ''}">${core.toFixed(1)}%</div>
                        </div>
                    `;
                });
                cpuCores.innerHTML = coresHtml;
            }

            // Memory Section
            const memOverview = document.getElementById('sysinfo-memory-overview');
            if (memOverview) {
                memOverview.innerHTML = `
                    <div class="sysinfo-big-bar">
                        <div class="sysinfo-big-bar-header">
                            <span class="sysinfo-big-bar-label">Arbeitsspeicher ( ${sysinfo.memory.used_gb} GB / ${sysinfo.memory.total_gb} GB )</span>
                            <span class="sysinfo-big-bar-value ${sysinfo.memory.status !== 'normal' ? 'text-' + sysinfo.memory.status : ''}">${sysinfo.memory.usage_percent}%</span>
                        </div>
                        <div class="sysinfo-bar-track">
                            <div class="sysinfo-bar-fill ${sysinfo.memory.status}" style="width: ${sysinfo.memory.usage_percent}%"></div>
                        </div>
                    </div>
                    <div class="sysinfo-detail-grid">
                         <div class="sysinfo-item">
                            <span class="sysinfo-item-label">Verfügbar / Frei</span>
                            <span class="sysinfo-item-value">${sysinfo.memory.available_gb} GB / ${sysinfo.memory.free_gb} GB</span>
                        </div>
                        <div class="sysinfo-item">
                            <span class="sysinfo-item-label">Swap (Auslagerungsdatei)</span>
                            <span class="sysinfo-item-value">${sysinfo.memory.swap.usage_percent}% (${sysinfo.memory.swap.used_gb} GB von ${sysinfo.memory.swap.total_gb} GB)</span>
                        </div>
                    </div>
                `;
            }

            // Disk Section
            const diskOverview = document.getElementById('sysinfo-disk-overview');
            if (diskOverview) {
                // Wir nehmen vereinfacht die erste Partition (häufig Systemlaufwerk)
                const mainDisk = sysinfo.disk.partitions.length > 0 ? sysinfo.disk.partitions[0] : null;

                if (mainDisk) {
                    diskOverview.innerHTML = `
                         <div class="sysinfo-big-bar">
                            <div class="sysinfo-big-bar-header">
                                <span class="sysinfo-big-bar-label">Systemlaufwerk (${mainDisk.mountpoint}) [${mainDisk.fstype}]</span>
                                <span class="sysinfo-big-bar-value ${sysinfo.disk.status !== 'normal' ? 'text-' + sysinfo.disk.status : ''}">${mainDisk.usage_percent}%</span>
                            </div>
                            <div class="sysinfo-bar-track">
                                <div class="sysinfo-bar-fill ${sysinfo.disk.status}" style="width: ${mainDisk.usage_percent}%"></div>
                            </div>
                        </div>
                        <div class="sysinfo-detail-grid">
                             <div class="sysinfo-item">
                                <span class="sysinfo-item-label">Speicher Belegt</span>
                                <span class="sysinfo-item-value">${mainDisk.used_gb} GB</span>
                            </div>
                            <div class="sysinfo-item">
                                <span class="sysinfo-item-label">Speicher Frei</span>
                                <span class="sysinfo-item-value">${mainDisk.free_gb} GB</span>
                            </div>
                            <div class="sysinfo-item">
                                <span class="sysinfo-item-label">Speicher Gesamt</span>
                                <span class="sysinfo-item-value">${mainDisk.total_gb} GB</span>
                            </div>
                        </div>
                    `;
                } else {
                    diskOverview.innerHTML = '<p class="text-muted">Keine Festplatteninformationen verfügbar.</p>';
                }
            }

            // Netzwerk Section
            const netOverview = document.getElementById('sysinfo-network-overview');
            if (netOverview) {
                // Nur das erste Interface mit IPv4 anzeigen der Einfachheit halber
                const iface = sysinfo.network.interfaces.length > 0 ? sysinfo.network.interfaces[0] : null;

                let ifaceHtml = '<p class="text-muted">Keine Interfaces gefunden.</p>';
                if (iface) {
                    const IPv4 = iface.addresses.find(a => a.type === 'IPv4');
                    const ipSpan = IPv4 ? IPv4.address : 'N/A';
                    
                    ifaceHtml = `
                        <div class="sysinfo-detail-grid">
                            <div class="sysinfo-item">
                                <span class="sysinfo-item-label">Interface Name</span>
                                <span class="sysinfo-item-value">${iface.name}</span>
                            </div>
                            <div class="sysinfo-item">
                                <span class="sysinfo-item-label">Lokale IP</span>
                                <span class="sysinfo-item-value font-mono">${ipSpan}</span>
                            </div>
                             <div class="sysinfo-item">
                                <span class="sysinfo-item-label">Link Status</span>
                                <span class="sysinfo-item-value">${iface.is_up ? '<span class="text-online">UP</span>' : '<span class="text-offline">DOWN</span>'}</span>
                            </div>
                        </div>
                    `;
                    // Wenn Traffic daten vorhanden
                    if(iface.bytes_sent !== undefined) {
                         ifaceHtml += `
                         <div class="sysinfo-detail-grid" style="margin-top: 8px;">
                            <div class="sysinfo-item">
                                <span class="sysinfo-item-label">Gesendet</span>
                                <span class="sysinfo-item-value">${window.Utils.formatBytes(iface.bytes_sent)}</span>
                            </div>
                            <div class="sysinfo-item">
                                <span class="sysinfo-item-label">Empfangen</span>
                                <span class="sysinfo-item-value">${window.Utils.formatBytes(iface.bytes_recv)}</span>
                            </div>
                        </div>
                         `;
                    }
                }
                netOverview.innerHTML = ifaceHtml;
            }

            // Uptime Section
            const uptimeOverview = document.getElementById('sysinfo-uptime-overview');
            if (uptimeOverview) {
                uptimeOverview.innerHTML = `
                    <div class="sysinfo-item" style="text-align: center; padding: var(--space-base);">
                        <span class="sysinfo-item-label" style="font-size: 12px; margin-bottom: 8px;">System Betriebszeit</span>
                        <span class="font-mono text-xl font-bold color-text-primary" style="display:block;">${sysinfo.uptime.formatted}</span>
                        <span class="text-xs text-muted" style="display:block; margin-top: 4px;">Boot Zeit: ${new Date(sysinfo.uptime.boot_time).toLocaleString('de-DE')}</span>
                    </div>
                `;
            }

            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'flex';
            this.notifications.log('Systeminformationen erfolgreich geladen.', 'success');

        } catch (error) {
            loadingDiv.innerHTML = `<p class="text-offline">Fehler: ${error.message}</p>`;
            this.notifications.error('Sysinfo Fehler', error.message);
        }
    }

    /**
     * Zeigt Standort-Details im Modal
     * @param {string} locationId 
     */
    showLocationModal(locationId) {
        // Daten besorgen
        let data = this.state.config.locations[locationId];
        if (this.state.statusData && this.state.statusData.locations[locationId]) {
            data = Object.assign({}, data, this.state.statusData.locations[locationId]);
        }
        
        if (!data) return;

        const isOnline = data.status === 'online';
        const titleEl = document.getElementById('modal-location-title');
        const contentEl = document.getElementById('location-detail-content');
        const pingBtn = document.getElementById('btn-location-ping');
        
        if(titleEl) titleEl.textContent = `Standort: ${data.name}`;

        // Event-Listener für den Ping-Button im Modal anpassen
        if(pingBtn) {
            const newPingBtn = pingBtn.cloneNode(true);
            pingBtn.parentNode.replaceChild(newPingBtn, pingBtn);
            newPingBtn.addEventListener('click', () => {
                this.ui.closeModal('modal-location');
                setTimeout(() => this.executePing(locationId), 300); // Kurz warten bis Modal zu ist
            });
        }

        // Services HTML
        let servicesHtml = '<p class="text-muted text-sm">Keine Services definiert.</p>';
        if (data.services && data.services.length > 0) {
            servicesHtml = '<div class="location-services-list">';
            data.services.forEach(srv => {
                const isRunning = srv.status === 'running';
                servicesHtml += `
                    <div class="location-service-item">
                        <div class="location-service-name">
                            <i class="fas ${isRunning ? 'fa-check-circle text-online' : 'fa-times-circle text-offline'}"></i>
                            ${srv.name}
                        </div>
                        <div class="location-service-port">Port: ${srv.port}</div>
                        <div class="location-service-status ${isRunning ? 'running' : 'stopped'}">
                            ${isRunning ? 'RUNNING' : 'STOPPED'}
                        </div>
                    </div>
                `;
            });
            servicesHtml += '</div>';
        }

        contentEl.innerHTML = `
            <div class="location-detail-header">
                <div class="location-detail-status-icon ${isOnline ? 'online' : 'offline'}">
                    <i class="fas ${isOnline ? 'fa-server' : 'fa-building'}"></i>
                </div>
                <div class="location-detail-info">
                    <h3>${data.name}</h3>
                    <p>${data.description || ''}</p>
                </div>
            </div>

            <div class="location-detail-grid">
                <div class="location-detail-item">
                    <div class="location-detail-item-label">Status</div>
                    <div class="location-detail-item-value ${isOnline? 'text-online' : 'text-offline'} font-bold">${isOnline ? 'ONLINE' : 'OFFLINE'}</div>
                </div>
                <div class="location-detail-item">
                    <div class="location-detail-item-label">IP Adresse</div>
                    <div class="location-detail-item-value font-mono">${data.ip_address}</div>
                </div>
                <div class="location-detail-item">
                    <div class="location-detail-item-label">Land</div>
                    <div class="location-detail-item-value">${data.country}</div>
                </div>
                <div class="location-detail-item">
                    <div class="location-detail-item-label">Datacenter</div>
                    <div class="location-detail-item-value">${data.datacenter}</div>
                </div>
                <div class="location-detail-item">
                    <div class="location-detail-item-label">Team</div>
                    <div class="location-detail-item-value">${data.team}</div>
                </div>
                <div class="location-detail-item">
                    <div class="location-detail-item-label">Koordinaten (Lat/Lng)</div>
                    <div class="location-detail-item-value font-mono">${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}</div>
                </div>
            </div>

            <div class="mt-base">
                <h4 class="text-sm font-semibold mb-sm">Überwachte Services</h4>
                ${servicesHtml}
            </div>
        `;

        this.ui.openModal('modal-location');
    }

    /**
     * Event Listener anlegen
     */
    _bindEvents() {
        // Main Actions
        const btnRefresh = document.getElementById('btn-refresh-status');
        const btnPingFfm = document.getElementById('btn-ping-frankfurt');
        const btnPingVie = document.getElementById('btn-ping-wien');
        const btnSysinfo = document.getElementById('btn-show-sysinfo');
        const btnSysinfoRefresh = document.getElementById('btn-sysinfo-refresh');

        if (btnRefresh) btnRefresh.addEventListener('click', () => this.refreshStatus());
        if (btnPingFfm) btnPingFfm.addEventListener('click', () => this.executePing('frankfurt'));
        if (btnPingVie) btnPingVie.addEventListener('click', () => this.executePing('wien'));
        if (btnSysinfo) btnSysinfo.addEventListener('click', () => this.showSystemInfo());
        if (btnSysinfoRefresh) btnSysinfoRefresh.addEventListener('click', () => this.showSystemInfo());

        // Auto Refresh Toggle
        const btnAuto = document.getElementById('btn-auto-refresh');
        const autoIndicator = document.getElementById('auto-refresh-indicator');
        
        if (btnAuto) {
            btnAuto.addEventListener('click', () => {
                this.state.autoRefresh = !this.state.autoRefresh;
                
                if (this.state.autoRefresh) {
                    autoIndicator.classList.add('active');
                    this.notifications.log('Auto-Refresh aktiviert.', 'info');
                    this._startTimers();
                } else {
                    autoIndicator.classList.remove('active');
                    this.notifications.log('Auto-Refresh deaktiviert.', 'warning');
                    clearInterval(this.state.timers.autoRefresh);
                    
                    // Progress Bar reset
                    const pb = document.getElementById('navbar-progress-bar');
                    if (pb) {
                        pb.style.transition = 'none';
                        pb.style.width = '0%';
                    }
                }
            });
        }

        // Custom Events from Map Popups
        document.addEventListener('pingLocation', (e) => this.executePing(e.detail));

        // Fullscreen Toggle (Optional, browser support varies)
        const btnFs = document.getElementById('btn-fullscreen');
        if (btnFs) {
            btnFs.addEventListener('click', () => {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(err => {
                        console.warn(`Error attempting to enable fullscreen: ${err.message}`);
                    });
                } else {
                    document.exitFullscreen();
                }
            });
        }
    }

    /**
     * Startet Hintergrund-Timer
     */
    _startTimers() {
        // Bestehenden Timer löschen falls vorhanden
        if (this.state.timers.autoRefresh) clearInterval(this.state.timers.autoRefresh);

        if (this.state.autoRefresh) {
            // Status Refresh Loop
            this.state.timers.autoRefresh = setInterval(() => {
                this.refreshStatus();
            }, this.state.refreshInterval);

            // Progress Bar Animation Helper
            this._animateProgressBar();
        }

        // System Health Refresh (alle 15s)
        if (!this.state.timers.sysHealth) {
             this.state.timers.sysHealth = setInterval(() => {
                 this.refreshSystemHealth();
             }, 15000);
        }
    }

    /**
     * Animiert den Fortschrittsbalken unter der Navbar passend zum Auto-Refresh Intervall
     */
    _animateProgressBar() {
        const pb = document.getElementById('navbar-progress-bar');
        if (!pb) return;

        const updateBar = () => {
            if (!this.state.autoRefresh) return;
            
            pb.style.transition = 'none';
            pb.style.width = '0%';
            
            // Reflow erzwingen
            void pb.offsetWidth;
            
            pb.style.transition = `width ${this.state.refreshInterval}ms linear`;
            pb.style.width = '100%';
        };

        updateBar();
        // Hook in den bestehenden Interval (etwas dirty, aber reicht für Demo)
        setInterval(() => {
            if (this.state.autoRefresh) updateBar();
        }, this.state.refreshInterval);
    }

    /**
     * Startet die UI Uhren
     */
    _startClock() {
        window.Utils.updateClock('clock-time', 'clock-date');
        this.state.timers.clock = setInterval(() => {
            window.Utils.updateClock('clock-time', 'clock-date');
        }, 1000);
        
        // Footer Init-Zeitpunkt setzen
        const footerStatus = document.getElementById('footer-connection-status');
        if(footerStatus) footerStatus.innerHTML = '<span class="status-dot status-dot-online"></span> Verbunden';
    }

    /**
     * Versteckt den Splash-Screen am Anfang
     */
    _hideLoadingScreen() {
        const ls = document.getElementById('loading-screen');
        const app = document.getElementById('app-container');
        
        if (ls && app) {
            setTimeout(() => {
                ls.classList.add('hidden');
                app.style.opacity = '1';
                
                // Sidebar Animationen triggern
                document.getElementById('sidebar-left')?.classList.add('animate-fade-in-right');
                document.getElementById('sidebar-right')?.classList.add('animate-fade-in-left');
                document.getElementById('dashboard-main')?.classList.add('animate-fade-in-up');
                
            }, 800); // Kurzer Delay für UX 
        }
    }
}

// Initialisierung bei DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    window.App = new Application();
    window.App.init();
});
