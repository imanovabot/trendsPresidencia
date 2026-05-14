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
let favorites = JSON.parse(localStorage.getItem('trends_favorites') || '[]');
let currentTheme = localStorage.getItem('trends_theme') || 'light';

// Chart instance storage
let trendsChart = null;

// ============================================
// INIT
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    applyTheme(currentTheme);
    initThemeToggle();
    initFavoritesButtons();
    await loadData();
    initUI();
    renderList();
    setupEventListeners();
    updateFavoritesUI();
});

// ============================================
// CONFIGURACIÓN
// ============================================

// Backend API URL — ajustar según despliegue
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8001'
    : 'http://187.77.14.245:8001';  // Producción: IP del servidor

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
            color: c.color || '#3b82f6',
            sources: {
                google_trends: c.sources?.google_trends || 0,
                youtube: c.sources?.youtube || 0,
                tiktok: c.sources?.tiktok || 0,
                x: c.sources?.x || 0,
                instagram: c.sources?.instagram || 0,
                sentiment: c.sources?.sentiment || 0,
            },
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
// THEME MANAGEMENT
// ============================================

function initThemeToggle() {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;
    btn.addEventListener('click', () => {
        currentTheme = currentTheme === 'light' ? 'dark' : 'light';
        applyTheme(currentTheme);
        localStorage.setItem('trends_theme', currentTheme);
    });
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = theme === 'light' ? '🌙' : '☀️';
}

// ============================================
// FAVORITES MANAGEMENT
// ============================================

function toggleFavorite(candidateId) {
    const idx = favorites.indexOf(candidateId);
    if (idx === -1) favorites.push(candidateId);
    else favorites.splice(idx, 1);
    localStorage.setItem('trends_favorites', JSON.stringify(favorites));
    renderList();
    updateFavoritesUI();
}

function isFavorite(candidateId) {
    return favorites.includes(candidateId);
}

function updateFavoritesUI() {
    const countEl = document.getElementById('favoritesCount');
    if (countEl) countEl.textContent = favorites.length;
}

function initFavoritesButtons() {
    // Event delegation for favorite buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('favorite-btn')) {
            const candidateId = e.target.dataset.candidateId;
            if (candidateId) toggleFavorite(candidateId);
        }
    });
}

// ============================================
// CSV EXPORT
// ============================================

function exportToCSV() {
    if (!filteredCandidates.length) return;

    const headers = ['Nombre', 'Partido', 'Momentum', 'Cambio 24h', 'Google Trends', 'YouTube', 'TikTok', 'X/Twitter', 'Instagram', 'Sentimiento'];
    const rows = filteredCandidates.map(c => [
        c.name,
        c.party,
        c.momentum.toFixed(1),
        c.change_24h.toFixed(1),
        c.sources.google_trends,
        c.sources.youtube,
        c.sources.tiktok,
        c.sources.x,
        c.sources.instagram,
        c.sources.sentiment.toFixed(1)
    ]);

    const csvContent = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `trends_presidencia_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
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

    // CSV Export button (delegated)
    document.addEventListener('click', (e) => {
        if (e.target.id === 'exportCsvBtn' || e.target.closest('#exportCsvBtn')) {
            e.stopPropagation();
            exportToCSV();
        }
    });
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
        const favClass = isFavorite(candidate.id) ? 'favorite-active' : '';

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
                <button class="favorite-btn ${favClass}" data-candidate-id="${candidate.id}" title="Marcar como favorito">
                    ${isFavorite(candidate.id) ? '★' : '☆'}
                </button>
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
    const tiktokPct = (candidate.sources.tiktok / maxVal) * 100;
    const xPct = (candidate.sources.x / maxVal) * 100;
    const instagramPct = (candidate.sources.instagram / maxVal) * 100;
    const sentPct = (candidate.sources.sentiment / 100) * 100;

    // Sentiment breakdown
    const { positive, neutral, negative } = candidate.sentiment_breakdown;
    const total = positive + neutral + negative;

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
            <button id="exportCsvBtn" class="export-csv-btn" data-candidate-id="${candidate.id}">
                📥 Exportar CSV
            </button>
        </div>

        <div class="chart-section">
            <h3>📈 Evolución de Tendencia (7 días)</h3>
            <div class="chart-container">
                <canvas id="trendsChart"></canvas>
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
                    <div class="source-label">TikTok</div>
                    <div class="source-value" style="color: #000000">${candidate.sources.tiktok}</div>
                    <div class="source-bar-container">
                        <div class="source-bar-fill tiktok" style="width: ${tiktokPct}%"></div>
                    </div>
                </div>
                <div class="source-item">
                    <div class="source-label">X/Twitter</div>
                    <div class="source-value" style="color: #1da1f2">${candidate.sources.x}</div>
                    <div class="source-bar-container">
                        <div class="source-bar-fill x" style="width: ${xPct}%"></div>
                    </div>
                </div>
                <div class="source-item">
                    <div class="source-label">Instagram</div>
                    <div class="source-value" style="color: #e1306c">${candidate.sources.instagram}</div>
                    <div class="source-bar-container">
                        <div class="source-bar-fill instagram" style="width: ${instagramPct}%"></div>
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

    // Render Chart and setup export button after DOM injection
    renderTrendsChart(candidate);
    setupExportButton();
}

// ============================================
// CHART.JS — TRENDS CHART
// ============================================

function renderTrendsChart(candidate) {
    const ctx = document.getElementById('trendsChart');
    if (!ctx) return;

    // Destroy previous chart if exists
    if (trendsChart) {
        trendsChart.destroy();
    }

    // Generate 7 days of mock historical data
    const labels = [];
    const data = [];
    const baseValue = candidate.sources.google_trends || 50;

    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('es-CO', { weekday: 'short', day: 'numeric' }));
        const variation = (Math.random() - 0.5) * 20;
        data.push(Math.max(0, Math.min(100, baseValue + variation)));
    }

    const theme = currentTheme;
    const gridColor = theme === 'dark' ? '#374151' : '#e5e7eb';
    const textColor = theme === 'dark' ? '#f3f4f6' : '#1f2937';

    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Índice de Tendencia',
                data,
                borderColor: candidate.color,
                backgroundColor: candidate.color + '20',
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointBackgroundColor: candidate.color,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: { color: textColor }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: gridColor },
                    ticks: { color: textColor }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: textColor }
                }
            }
        }
    });
}

// ============================================
// CSV EXPORT HANDLER
// ============================================

function setupExportButton() {
    const exportBtn = document.getElementById('exportCsvBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            exportToCSV();
        });
    }
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
