/**
 * trendsPresidencia — App principal
 * Funcionalidad: pronóstico segunda vuelta Abelardo vs Cepeda
 * Sin dependencias, vanilla JS
 */

// ============================================
// STATE
// ============================================

let candidates = [];

// ============================================
// INIT
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    await loadCandidates();
    await loadRunoffForecast();
    renderMetricsGrid();
    setupEventListeners();
});

// ============================================
// CONFIGURACIÓN
// ============================================

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8001'
    : '';

// ============================================
// DATA LOADING
// ============================================

async function loadCandidates() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/candidates`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        // Filtrar solo Abelardo y Cepeda
        candidates = data.candidates.filter(c =>
            c.name.includes('Abelardo') || c.name.includes('Cepeda')
        ).map(c => ({
            ...c,
            id: c.id || c.name.toLowerCase().replace(/\s+/g, '-'),
            momentum: c.momentum || 0,
            change_24h: c.change_24h || 0,
            color: c.color || '#3b82f6',
            sources: c.sources || { google_trends: 0, youtube: 0, sentiment: 0 }
        }));

        console.log(`✅ Cargados ${candidates.length} candidatos (segunda vuelta)`);
    } catch (error) {
        console.error('❌ Error cargando candidatos:', error);
        candidates = [];
    }
}

// ============================================
// RUNOFF FORECAST
// ============================================

async function loadRunoffForecast() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/runoff/forecast`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const forecast = await response.json();

        if (forecast.error || !forecast.predictions) {
            console.warn('⚠️ No hay pronóstico de segunda vuelta');
            showError('No hay pronóstico disponible');
            return;
        }

        // Actualizar porcentajes
        const abelardoPct = forecast.predictions['Abelardo de la Espriella'] || 0;
        const cepedaPct = forecast.predictions['Iván Cepeda'] || 0;

        document.getElementById('abelardoPct').textContent = `${abelardoPct}%`;
        document.getElementById('cepedaPct').textContent = `${cepedaPct}%`;
        document.getElementById('abelardoBar').style.width = `${abelardoPct}%`;
        document.getElementById('cepedaBar').style.width = `${cepedaPct}%`;

        // Actualizar timestamp
        if (forecast.timestamp) {
            const date = new Date(forecast.timestamp);
            document.getElementById('lastUpdate').textContent =
                `Actualizado: ${date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}`;
        }

        console.log('✅ Pronóstico cargado:', { abelardo: abelardoPct, cepeda: cepedaPct });
    } catch (error) {
        console.error('Error cargando pronóstico:', error);
        showError('Error al cargar el pronóstico');
    }
}

// ============================================
// RENDER METRICS GRID
// ============================================

function renderMetricsGrid() {
    const grid = document.getElementById('metricsGrid');
    if (!grid) return;

    if (candidates.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No hay datos disponibles</p>';
        return;
    }

    grid.innerHTML = candidates.map(candidate => {
        const changeClass = candidate.change_24h >= 0 ? 'change-positive' : 'change-negative';
        const changeIcon = candidate.change_24h >= 0 ? '▲' : '▼';
        const changeValue = Math.abs(candidate.change_24h).toFixed(1);
        const color = candidate.color;

        return `
            <div class="metric-card" style="--metric-color: ${color}">
                <div class="metric-header">
                    <div>
                        <div class="metric-name">${candidate.name}</div>
                        <div class="metric-party">${candidate.party}</div>
                    </div>
                    <div class="metric-value" style="color: ${color}">${candidate.momentum.toFixed(1)}%</div>
                </div>
                <div class="metric-details">
                    <div>
                        <span>Cambio 24h:</span>
                        <strong class="${changeClass}">${changeIcon} ${changeValue}%</strong>
                    </div>
                    <div>
                        <span>Google Trends:</span>
                        <strong>${candidate.sources?.google_trends || 0}</strong>
                    </div>
                    <div>
                        <span>YouTube:</span>
                        <strong>${candidate.sources?.youtube || 0}</strong>
                    </div>
                    <div>
                        <span>Sentimiento:</span>
                        <strong>${(candidate.sources?.sentiment || 0).toFixed(1)}%</strong>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }

    const modal = document.getElementById('methodologyModal');
    const link = document.getElementById('methodologyLink');
    const closeBtn = document.getElementById('closeModal');

    if (link && modal) {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            modal.showModal();
        });
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => modal.close());
    }

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.close();
        });
    }
}

// ============================================
// REFRESH
// ============================================

async function handleRefresh() {
    const refreshBtn = document.querySelector('.refresh-btn');
    if (!refreshBtn) return;

    refreshBtn.disabled = true;
    refreshBtn.textContent = '🔄 Actualizando...';

    try {
        const response = await fetch('/api/v1/candidates/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        // Recargar todo
        await loadCandidates();
        await loadRunoffForecast();
        renderMetricsGrid();

        showNotification('✅ Datos actualizados correctamente');
    } catch (error) {
        console.error('Error:', error);
        showNotification(`❌ Error: ${error.message}`, 'error');
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = '🔄 Actualizar';
    }
}

// ============================================
// HELPERS
// ============================================

function showError(message) {
    const grid = document.getElementById('metricsGrid');
    if (grid) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <p style="color: var(--text-muted);">${message}</p>
            </div>
        `;
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        z-index: 2000;
        animation: slideIn 0.3s ease;
        font-size: 0.9rem;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Exponer funciones globales
window.refreshAnalysis = handleRefresh;
