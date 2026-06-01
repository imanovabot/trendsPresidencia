/**
 * trendsPresidencia — App principal
 * Funcionalidad: búsqueda, filtrado, detalle de candidatos
 * Sin dependencias, vanilla JS
 */

// ============================================
// STATE
// ============================================

let allCandidates = [];
let filteredCandidates = [];
let selectedCandidateId = null;
let currentCategory = 'Todos';

// ============================================
// INIT
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    initUI();
    renderList();
    setupEventListeners();
});

// ============================================
// CONFIGURACIÓN
// ============================================

const API_BASE_URL = '/api';  // Rutas relativas para que nginx proxee

// ============================================
// DATA LOADING
// ============================================

async function loadData() {
    try {
        // Intentar cargar desde API primero
        const response = await fetch(`${API_BASE_URL}/api/v1/candidates`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        allCandidates = data.candidates.map((c, idx) => ({
            ...c,
            id: c.id || c.name.toLowerCase().replace(/\s+/g, '-'),
            change_24h: c.change_24h || 0,
            color: c.color || '#3b82f6'
        }));
        filteredCandidates = [...allCandidates];

        // Actualizar última actualización
        const lastUpdateEl = document.getElementById('lastUpdate');
        if (lastUpdateEl && data.last_updated) {
            const date = new Date(data.last_updated);
            lastUpdateEl.textContent = date.toLocaleString('es-CO');
        }

        // Actualizar frecuencia
        const freqEl = document.getElementById('updateFreq');
        if (freqEl) freqEl.textContent = '6h';

        console.log(`✅ Cargados ${allCandidates.length} candidatos desde API`);
    } catch (error) {
        console.warn('⚠️ API no disponible, cargando datos estáticos:', error.message);
        // Fallback a JSON estático
        try {
            const response = await fetch('data/candidates.json');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            allCandidates = data.candidates;
            filteredCandidates = [...allCandidates];
            console.log(`✅ Cargados ${allCandidates.length} candidatos desde JSON estático`);
        } catch (fallbackError) {
            console.error('❌ Error cargando datos estáticos:', fallbackError);
            showError('No se pudieron cargar los datos. Verifica la conexión.');
        }
    }
}

// ============================================
// UI INITIALIZATION
// ============================================

function initUI() {
    const categoryFilter = document.getElementById('categoryFilter');
    if (!categoryFilter) return;

    // Obtener categorías únicas desde los datos
    const categories = ['Todos'];
    allCandidates.forEach(c => {
        if (!categories.includes(c.party)) categories.push(c.party);
    });

    // Populate select
    categoryFilter.innerHTML = categories
        .map(cat => `<option value="${cat}">${cat}</option>`)
        .join('');

    // Set initial category
    currentCategory = 'Todos';
    categoryFilter.value = 'Todos';
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    // Search input (debounced)
    const searchInput = document.getElementById('searchInput');
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            filterCandidates(e.target.value, currentCategory);
        }, 200);
    });

    // Category filter
    const categoryFilter = document.getElementById('categoryFilter');
    categoryFilter.addEventListener('change', (e) => {
        currentCategory = e.target.value;
        const searchValue = document.getElementById('searchInput').value;
        filterCandidates(searchValue, currentCategory);
    });

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
// FILTERING LOGIC
// ============================================

function filterCandidates(searchQuery, category) {
    const query = searchQuery.toLowerCase().trim();

    filteredCandidates = allCandidates.filter(candidate => {
        // Category filter
        const matchesCategory = category === 'Todos' || candidate.party === category;

        // Search filter (name, party, description)
        const matchesSearch = !query ||
            candidate.name.toLowerCase().includes(query) ||
            candidate.party.toLowerCase().includes(query) ||
            candidate.description.toLowerCase().includes(query);

        return matchesCategory && matchesSearch;
    });

    renderList();
}

// ============================================
// RENDERING
// ============================================

function renderList() {
    const listContainer = document.getElementById('candidateList');
    const statsEl = document.getElementById('resultStats');

    if (!listContainer) return;

    // Update stats
    statsEl.textContent = `Mostrando ${filteredCandidates.length} candidato${filteredCandidates.length !== 1 ? 's' : ''}`;

    // Clear list
    listContainer.innerHTML = '';

    if (filteredCandidates.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1; padding: 3rem;">
                <div class="empty-icon">🔍</div>
                <h3>No se encontraron candidatos</h3>
                <p>Intenta con otros términos de búsqueda o ajusta el filtro de categoría.</p>
            </div>
        `;
        return;
    }

    // Render each candidate card
    filteredCandidates.forEach(candidate => {
        const card = document.createElement('div');
        card.className = `candidate-card ${selectedCandidateId === candidate.id ? 'active' : ''}`;
        card.onclick = () => selectCandidate(candidate.id);

        const changeClass = candidate.change_24h >= 0 ? 'change-positive' : 'change-negative';
        const changeIcon = candidate.change_24h >= 0 ? '▲' : '▼';
        const changeValue = Math.abs(candidate.change_24h).toFixed(1);

        card.innerHTML = `
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
                    <div class="source-bar trends" title="Google Trends: ${candidate.sources.google_trends}"></div>
                    <div class="source-bar youtube" title="YouTube: ${candidate.sources.youtube}"></div>
                    <div class="source-bar sentiment" title="Sentimiento: ${candidate.sources.sentiment}"></div>
                </div>
            </div>
        `;

        listContainer.appendChild(card);
    });
}

// ============================================
// CANDIDATE SELECTION & DETAIL
// ============================================

function selectCandidate(candidateId) {
    selectedCandidateId = candidateId;
    renderList(); // Re-render to update active state

    const candidate = allCandidates.find(c => c.id === candidateId);
    if (!candidate) return;

    renderDetail(candidate);
}

function renderDetail(candidate) {
    const emptyState = document.getElementById('emptyState');
    const detailPanel = document.getElementById('candidateDetail');

    emptyState.style.display = 'none';
    detailPanel.style.display = 'block';

    const changeClass = candidate.change_24h >= 0 ? 'momentum-up' : 'momentum-down';
    const changeIcon = candidate.change_24h >= 0 ? '▲' : '▼';
    const changeValue = Math.abs(candidate.change_24h).toFixed(1);

    // Normalize source values for bars (0-100 scale assumed)
    const maxVal = 100;
    const trendsPct = (candidate.sources.google_trends / maxVal) * 100;
    const ytPct = (candidate.sources.youtube / maxVal) * 100;
    const sentPct = (candidate.sources.sentiment / 100) * 100;

    // Sentiment breakdown
    const { positive, neutral, negative } = candidate.sentiment_breakdown;
    const total = positive + neutral + negative;

    // Nuevos datos electorales
    const stability = candidate.historical_stability || 2.5;
    const stabilityClass = stability < 2.0 ? 'stable' : stability < 3.0 ? 'moderate' : 'volatile';
    const noiseDetection = candidate.noise_detection || {};
    const isNoise = noiseDetection.is_shock || false;
    const relatedQueries = candidate.related_queries || [];
    const regionalData = candidate.regional_distribution || {};

    detailPanel.innerHTML = `
        <div class="detail-header">
            <div class="detail-title">
                <h2>${candidate.name}</h2>
                <div class="detail-party">${candidate.party}</div>
            </div>
            <div class="detail-momentum">
                <span class="value" style="color: ${candidate.color}">
                    ${candidate.momentum.toFixed(1)}%
                </span>
                <div class="change ${changeClass}">
                    ${changeIcon} ${changeValue}% (24h)
                </div>
            </div>
        </div>

        <div class="sources-section">
            <h3>Desglose por Fuente</h3>
            <div class="sources-grid">
                <div class="source-item">
                    <div class="source-label">Google Trends</div>
                    <div class="source-value" style="color: #8b5cf6">${candidate.sources.google_trends}</div>
                    <div class="source-bar-container">
                        <div class="source-bar-fill trends" style="width: ${trendsPct}%"></div>
                    </div>
                </div>
                <div class="source-item">
                    <div class="source-label">YouTube</div>
                    <div class="source-value" style="color: #ef4444">${candidate.sources.youtube}</div>
                    <div class="source-bar-container">
                        <div class="source-bar-fill youtube" style="width: ${ytPct}%"></div>
                    </div>
                </div>
                <div class="source-item">
                    <div class="source-label">Sentimiento</div>
                    <div class="source-value" style="color: #3b82f6">${candidate.sources.sentiment.toFixed(1)}</div>
                    <div class="source-bar-container">
                        <div class="source-bar-fill sentiment" style="width: ${sentPct}%"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- NUEVA SECCIÓN: Análisis Electoral Avanzado -->
        <div class="electoral-analysis-section">
            <h3>📊 Análisis Electoral</h3>

            <!-- Estabilidad -->
            <div class="analysis-card">
                <div class="analysis-label">Estabilidad de la Curva (Voto Duro)</div>
                <div class="stability-meter ${stabilityClass}">
                    <div class="stability-value" style="width: ${Math.min(stability * 10, 100)}%"></div>
                </div>
                <div class="analysis-detail">
                    <span class="stability-score">${stability}</span>
                    <span class="stability-text">${getStabilityText(stability)}</span>
                </div>
            </div>

            <!-- Ruido -->
            ${isNoise ? `
            <div class="analysis-card noise-warning">
                <div class="analysis-label">⚠️ Ruido Detectado</div>
                <p>${noiseDetection.interpretation || 'Pico anómalo en las últimas horas'}</p>
                <small>Z-score: ${noiseDetection.z_score || 'N/A'}</small>
            </div>
            ` : `
            <div class="analysis-card noise-ok">
                <div class="analysis-label">✅ Sin Ruido</div>
                <p>El interés es estable y representativo del electorado real.</p>
            </div>
            `}

            <!-- Consultas Relacionadas -->
            <div class="analysis-card">
                <div class="analysis-label">🔍 Consultas Relacionadas</div>
                ${relatedQueries.length > 0 ? `
                <div class="queries-list">
                    ${relatedQueries.slice(0, 5).map(q => {
                        const isElectoral = !['stream', 'clip', 'memes', 'video', 'youtube', 'westcol'].some(kw => q.toLowerCase().includes(kw));
                        return `<span class="query-tag ${isElectoral ? 'electoral' : 'noise'}">${q}</span>`;
                    }).join('')}
                </div>
                ` : '<p class="text-muted">Sin consultas relacionadas disponibles</p>'}
            </div>

            <!-- Distribución Regional -->
            ${Object.keys(regionalData).length > 0 ? `
            <div class="analysis-card">
                <div class="analysis-label">🗺️ Interés por Región</div>
                <div class="regional-bars">
                    ${Object.entries(regionalData)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 5)
                        .map(([region, value]) => `
                        <div class="region-row">
                            <span class="region-name">${region}</span>
                            <div class="region-bar-container">
                                <div class="region-bar" style="width: ${value}%"></div>
                            </div>
                            <span class="region-value">${value}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        </div>

        <div class="sentiment-section">
            <h3>Distribución de Sentimiento</h3>
            <div class="sentiment-bars">
                <div class="sentiment-bar-row">
                    <span class="sentiment-label">Positivo</span>
                    <div class="sentiment-track">
                        <div class="sentiment-fill positive" style="width: ${positive}%"></div>
                    </div>
                    <span class="sentiment-value">${positive}%</span>
                </div>
                <div class="sentiment-bar-row">
                    <span class="sentiment-label">Neutral</span>
                    <div class="sentiment-track">
                        <div class="sentiment-fill neutral" style="width: ${neutral}%"></div>
                    </div>
                    <span class="sentiment-value">${neutral}%</span>
                </div>
                <div class="sentiment-bar-row">
                    <span class="sentiment-label">Negativo</span>
                    <div class="sentiment-track">
                        <div class="sentiment-fill negative" style="width: ${negative}%"></div>
                    </div>
                    <span class="sentiment-value">${negative}%</span>
                </div>
            </div>
        </div>

        <div class="news-section">
            <h3>📰 Noticias Relevantes</h3>
            <div class="news-list">
                ${candidate.top_news.map(news => `
                    <div class="news-item">${news}</div>
                `).join('')}
            </div>
        </div>

        <div class="description-section">
            <h3>📝 Resumen</h3>
            <p style="color: var(--text-secondary); line-height: 1.6;">
                ${candidate.description}
            </p>
        </div>
    `;
}

// ============================================
// NUEVAS FUNCIONES AUXILIARES
// ============================================

function getStabilityText(stability) {
    if (stability < 1.5) return "Muy estable — bases disciplinadas (ej: Cepeda 2022)";
    if (stability < 3.0) return "Estable — combinación de voto duro + indecisos";
    if (stability < 5.0) return "Moderadamente volátil — depende de eventos regionales";
    return "Muy volátil — sensible a shocks (streams, noticias)";
}

// ============================================
// ERROR HANDLING
// ============================================

function showError(message) {
    const listContainer = document.getElementById('candidateList');
    if (listContainer) {
        listContainer.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-icon">⚠️</div>
                <h3>Error</h3>
                <p>${message}</p>
            </div>
        `;
    }
}
