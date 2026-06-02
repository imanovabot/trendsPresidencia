/**
 * trendsPresidencia — App principal
 * Funcionalidad: pronóstico segunda vuelta, desglose candidatos, lista candidatos
 * Sin dependencias, vanilla JS
 */

// ============================================
// STATE
// ============================================

let allCandidates = [];
let runoffForecast = null;

// ============================================
// INIT
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    await loadRunoffForecast();
    renderCandidatesGrid();
    renderCandidatesList();
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

async function loadData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/candidates`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        allCandidates = data.candidates.map(c => ({
            ...c,
            id: c.id || c.name.toLowerCase().replace(/\s+/g, '-'),
            momentum: c.momentum || 0,
            change_24h: c.change_24h || 0,
            color: c.color || '#3b82f6',
            sources: c.sources || { google_trends: 0, youtube: 0, sentiment: 0 }
        }));

        console.log(`✅ Cargados ${allCandidates.length} candidatos`);
    } catch (error) {
        console.warn('⚠️ API no disponible, cargando datos estáticos:', error.message);
        try {
            const response = await fetch('data/candidates.json');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            allCandidates = data.candidates.map(c => ({
                ...c,
                id: c.id || c.name.toLowerCase().replace(/\s+/g, '-')
            }));
            console.log(`✅ Cargados ${allCandidates.length} candidatos desde JSON estático`);
        } catch (fallbackError) {
            console.error('❌ Error cargando datos:', fallbackError);
        }
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
            hidePredictionPanel();
            return;
        }

        runoffForecast = forecast;
        showPredictionPanel(forecast);
        updateLastUpdate(forecast.timestamp);
        console.log('✅ Pronóstico de segunda vuelta cargado');
    } catch (error) {
        console.error('Error cargando pronóstico:', error);
        hidePredictionPanel();
    }
}

function showPredictionPanel(forecast) {
    const abelardo = forecast.predictions['Abelardo de la Espriella'] || 0;
    const cepeda = forecast.predictions['Iván Cepeda'] || 0;

    document.getElementById('abelardoPct').textContent = `${abelardo}%`;
    document.getElementById('cepedaPct').textContent = `${cepeda}%`;
    document.getElementById('abelardoBar').style.width = `${abelardo}%`;
    document.getElementById('cepedaBar').style.width = `${cepeda}%`;
    document.getElementById('predictionPanel').style.display = 'block';
}

function hidePredictionPanel() {
    document.getElementById('predictionPanel').style.display = 'none';
}

function updateLastUpdate(timestamp) {
    const el = document.getElementById('analysisLastUpdate');
    if (el && timestamp) {
        const date = new Date(timestamp);
        el.textContent = `Actualizado: ${date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
    }
}

// ============================================
// RENDER CANDIDATES GRID (Desglose)
// ============================================

function renderCandidatesGrid() {
    const grid = document.getElementById('candidatesGrid');
    if (!grid) return;

    // Solo mostrar Abelardo y Cepeda en el desglose de segunda vuelta
    const mainCandidates = allCandidates.filter(c =>
        c.name.includes('Abelardo') || c.name.includes('Cepeda')
    );

    if (mainCandidates.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No hay datos disponibles</p>';
        return;
    }

    grid.innerHTML = mainCandidates.map(candidate => `
        <div class="candidate-grid-card" style="--card-accent: ${candidate.color}">
            <div class="grid-header">
                <span class="grid-name">${candidate.name}</span>
                <span class="grid-pct" style="color: ${candidate.color}">${candidate.momentum.toFixed(1)}%</span>
            </div>
            <div class="grid-detail">
                <small>Momentum: ${candidate.momentum.toFixed(1)}%</small>
                <small>Cambio 24h: ${candidate.change_24h >= 0 ? '▲' : '▼'} ${Math.abs(candidate.change_24h).toFixed(1)}%</small>
            </div>
        </div>
    `).join('');
}

// ============================================
// RENDER CANDIDATES LIST
// ============================================

function renderCandidatesList() {
    const list = document.getElementById('candidateList');
    if (!list) return;

    if (allCandidates.length === 0) {
        list.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1; padding: 3rem;">
                <div class="empty-icon">🔍</div>
                <h3>No hay candidatos disponibles</h3>
            </div>
        `;
        return;
    }

    list.innerHTML = allCandidates.map(candidate => {
        const changeClass = candidate.change_24h >= 0 ? 'change-positive' : 'change-negative';
        const changeIcon = candidate.change_24h >= 0 ? '▲' : '▼';
        const changeValue = Math.abs(candidate.change_24h).toFixed(1);

        return `
            <div class="candidate-card" onclick="selectCandidate('${candidate.id}')">
                <div class="candidate-info">
                    <div class="candidate-name">${candidate.name}</div>
                    <div class="candidate-party">${candidate.party}</div>
                </div>
                <div class="candidate-metrics">
                    <div class="momentum-badge" style="color: ${candidate.color}">
                        ${candidate.momentum.toFixed(1)}%
                    </div>
                    <div class="change-indicator ${changeClass}">
                        ${changeIcon} ${changeValue}% (24h)
                    </div>
                    <div class="source-bars">
                        <div class="source-bar trends" title="Google Trends: ${candidate.sources?.google_trends || 0}"></div>
                        <div class="source-bar youtube" title="YouTube: ${candidate.sources?.youtube || 0}"></div>
                        <div class="source-bar sentiment" title="Sentimiento: ${candidate.sources?.sentiment || 0}"></div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// CANDIDATE SELECTION (para futura expansión)
// ============================================

function selectCandidate(candidateId) {
    // Por ahora solo marca como activo
    const candidate = allCandidates.find(c => c.id === candidateId);
    if (!candidate) return;

    console.log('Candidato seleccionado:', candidate.name);
    // Aquí se puede expandir para mostrar detalles en un modal o panel
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }

    // Methodology modal
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
        await loadData();
        renderCandidatesGrid();
        renderCandidatesList();
        await loadRunoffForecast();

        showNotification('✅ Datos actualizados correctamente');
    } catch (error) {
        console.error('Error:', error);
        showNotification(`❌ Error: ${error.message}`, 'error');
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = '🔄 Actualizar';
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

// Inicializar después de que todas las funciones estén definidas
window.selectCandidate = selectCandidate;
window.refreshAnalysis = handleRefresh;
