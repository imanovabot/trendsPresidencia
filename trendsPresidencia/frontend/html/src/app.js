/**
 * trendsPresidencia — App principal
 * Solo pronóstico de segunda vuelta (Abelardo vs Cepeda)
 * Sin dependencias, vanilla JS
 */

// ============================================
// STATE
// ============================================

let forecastData = null;
let candidates = [];

// ============================================
// INIT
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    await loadForecast();
    await loadCandidates();
    renderAll();
    setupEventListeners();
});

// ============================================
// CONFIG
// ============================================

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8001'
    : '';

// ============================================
// DATA LOADING
// ============================================

async function loadForecast() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/runoff/forecast`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        forecastData = await response.json();

        if (forecastData.error) {
            console.warn('Error en pronóstico:', forecastData.error);
            hideForecast();
            return;
        }

        showForecast();
        console.log('✅ Pronóstico cargado:', forecastData);
    } catch (error) {
        console.error('Error cargando pronóstico:', error);
        hideForecast();
    }
}

async function loadCandidates() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/candidates`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        // Solo Abelardo y Cepeda
        candidates = data.candidates.filter(c =>
            c.name.includes('Abelardo') || c.name.includes('Cepeda')
        ).map(c => ({
            ...c,
            momentum: c.momentum || 0,
            change_24h: c.change_24h || 0,
            color: c.color || '#3b82f6',
            sources: c.sources || { google_trends: 0 }
        }));

        console.log(`✅ Cargados ${candidates.length} candidatos`);
    } catch (error) {
        console.error('Error cargando candidatos:', error);
        candidates = [];
    }
}

// ============================================
// RENDERING
// ============================================

function renderAll() {
    renderForecast();
    renderMetrics();
    renderTechInfo();
}

function renderForecast() {
    if (!forecastData || !forecastData.predictions) return;

    const abelardo = forecastData.predictions['Abelardo de la Espriella'] || 0;
    const cepeda = forecastData.predictions['Iván Cepeda'] || 0;

    document.getElementById('abelardoPct').textContent = `${abelardo}%`;
    document.getElementById('cepedaPct').textContent = `${cepeda}%`;

    // Animar barras después de un pequeño delay
    setTimeout(() => {
        document.getElementById('abelardoBar').style.width = `${abelardo}%`;
        document.getElementById('cepedaBar').style.width = `${cepeda}%`;
    }, 100);

    // Actualizar timestamp
    if (forecastData.timestamp) {
        const date = new Date(forecastData.timestamp);
        document.getElementById('lastUpdate').textContent =
            `Actualizado: ${date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}`;
    }

    // Actualizar metodología
    if (forecastData.methodology) {
        document.getElementById('methodology').textContent = forecastData.methodology;
    }
}

function renderMetrics() {
    const grid = document.getElementById('metricsGrid');
    if (!grid) return;

    if (candidates.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); text-align: center; grid-column: 1/-1;">No hay datos disponibles</p>';
        return;
    }

    grid.innerHTML = candidates.map(c => {
        const changeClass = c.change_24h >= 0 ? 'change-positive' : 'change-negative';
        const changeIcon = c.change_24h >= 0 ? '▲' : '▼';
        const changeValue = Math.abs(c.change_24h).toFixed(1);
        const gt = c.sources?.google_trends || 0;

        return `
            <div class="metric-card" style="--metric-color: ${c.color}">
                <div class="metric-header">
                    <div>
                        <div class="metric-name">${c.name}</div>
                        <div class="metric-party">${c.party}</div>
                    </div>
                    <div class="metric-value" style="color: ${c.color}">${c.momentum.toFixed(1)}%</div>
                </div>
                <div class="metric-details">
                    <div>
                        <span>Cambio 24h:</span>
                        <strong class="${changeClass}">${changeIcon} ${changeValue}%</strong>
                    </div>
                    <div>
                        <span>Google Trends:</span>
                        <strong>${gt.toFixed(1)}</strong>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderTechInfo() {
    const container = document.getElementById('techInfo');
    if (!container || !forecastData) return;

    let html = '<h3>🔧 Información Técnica</h3>';

    if (forecastData.raw_scores) {
        html += '<div class="stats-row">';
        html += `<div class="stat-item">Abelardo GT: <code>${forecastData.raw_scores.Abelardo?.toFixed(1) || '--'}</code></div>`;
        html += `<div class="stat-item">Cepeda GT: <code>${forecastData.raw_scores.Cepeda?.toFixed(1) || '--'}</code></div>`;
        html += `<div class="stat-item">Fajardo GT: <code>${forecastData.raw_scores.Fajardo?.toFixed(1) || '--'}</code></div>`;
        html += `<div class="stat-item">Paloma GT: <code>${forecastData.raw_scores.Paloma?.toFixed(1) || '--'}</code></div>`;
        html += '</div>';
    }

    if (forecastData.stability) {
        html += '<div class="stats-row" style="margin-top: 0.5rem;">';
        html += `<div class="stat-item">Desviación Abelardo: <code>${forecastData.stability.Abelardo || '--'}</code></div>`;
        html += `<div class="stat-item">Desviación Cepeda: <code>${forecastData.stability.Cepeda || '--'}</code></div>`;
        html += `<div class="stat-item">Desviación Fajardo: <code>${forecastData.stability.Fajardo || '--'}</code></div>`;
        html += '</div>';
    }

    if (forecastData.margin !== undefined) {
        html += `<p style="margin-top: 1rem;"><strong>Margen:</strong> ${forecastData.margin}% | <strong>Ganador proyectado:</strong> ${forecastData.winner}</p>`;
    }

    container.innerHTML = html;
}

function showForecast() {
    document.getElementById('runoffForecast').style.display = 'block';
}

function hideForecast() {
    document.getElementById('runoffForecast').style.display = 'none';
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
    const btn = document.querySelector('.refresh-btn');
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = '🔄 Actualizando...';

    try {
        const response = await fetch('/api/v1/candidates/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        // Recargar datos
        forecastData = data.runoff_forecast || null;
        await loadCandidates();
        renderAll();

        showNotification('✅ Datos actualizados correctamente');
    } catch (error) {
        console.error('Error:', error);
        showNotification(`❌ Error: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 Actualizar';
    }
}

// ============================================
// NOTIFICATIONS
// ============================================

function showNotification(message, type = 'success') {
    const el = document.createElement('div');
    el.className = `notification ${type}`;
    el.textContent = message;
    el.style.cssText = `
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
    document.body.appendChild(el);

    setTimeout(() => {
        el.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => el.remove(), 300);
    }, 3000);
}

// Exponer funciones
window.refreshAnalysis = handleRefresh;
