/**
 * trendsPresidencia — Google Trends Embed para Segunda Vuelta
 * Renderiza el gráfico oficial de Google Trends usando el embed API
 */

(function() {
    'use strict';

    // Configuración de la segunda vuelta
    const CONFIG = {
        comparisonItem: [
            {
                keyword: "/g/11bwfmp95b",  // Abelardo de la Espriella
                geo: "CO",
                time: "now 7-d"
            },
            {
                keyword: "/g/1q6jc4dr2",  // Iván Cepeda
                geo: "CO",
                time: "now 7-d"
            }
        ],
        category: 0,
        property: "",
        exploreQuery: "date=now%207-d&geo=CO&q=%2Fg%2F11bwfmp95b,%2Fg%2F1q6jc4dr2"
    };

    // Estado
    let currentTimeframe = "now 7-d";
    let containerId = 'trends-second-round-container';

    // Función principal de renderizado
    function renderTrends() {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container #${containerId} not found`);
            return;
        }

        // Actualizar configuración
        CONFIG.comparisonItem.forEach(item => {
            item.time = currentTimeframe;
        });
        CONFIG.exploreQuery = `date=${encodeURIComponent(currentTimeframe)}&geo=CO&q=%2Fg%2F11bwfmp95b,%2Fg%2F1q6jc4dr2`;

        // Limpiar contenedor
        container.innerHTML = '';

        // Verificar que trends esté disponible
        if (typeof trends === 'undefined' || !trends.embed || !trends.embed.renderExploreWidget) {
            console.warn('trends.embed no disponible, reintentando en 1s...');
            setTimeout(renderTrends, 1000);
            return;
        }

        // Renderizar
        try {
            trends.embed.renderExploreWidget(
                "TIMESERIES",
                CONFIG,
                { exploreQuery: CONFIG.exploreQuery }
            );
            console.log(`✅ Trends embed actualizado: ${currentTimeframe}`);
        } catch (error) {
            console.error('Error renderizando Trends embed:', error);
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <p>Error al cargar Google Trends.</p>
                    <p><a href="https://trends.google.es/trends/explore?date=${encodeURIComponent(currentTimeframe)}&geo=CO&q=%2Fg%2F11bwfmp95b,%2Fg%2F1q6jc4dr2" 
                          target="_blank" 
                          style="color: var(--text-accent);">
                        Ver gráfico en Google Trends ↗
                    </a></p>
                </div>
            `;
        }
    }

    // Actualizar timeframe
    function updateTimeframe(timeframe) {
        currentTimeframe = timeframe;
        renderTrends();
    }

    // Exponer funciones globalmente
    window.updateTrendsTimeframe = updateTimeframe;
    window.refreshSecondRoundTrends = () => updateTimeframe("now 7-d");

    // Auto-render cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(renderTrends, 500);
        });
    } else {
        setTimeout(renderTrends, 500);
    }

    // Re-renderizar cuando la ventana cambie de tamaño (el embed se adapte)
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(renderTrends, 300);
    });

})();
