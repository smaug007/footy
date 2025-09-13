/**
 * Enhanced JavaScript functionality for Phase 3 BTTS Dashboard
 * Sophisticated prediction system with advanced visualizations
 */

/* ============================================
   ENHANCED PHASE 3 JAVASCRIPT FUNCTIONALITY
   Sophisticated BTTS Dashboard Features
   ============================================ */

/**
 * Enhanced Dashboard Manager for Phase 3 features
 */
class EnhancedDashboardManager {
    constructor() {
        this.activeFilters = {};
        this.realTimeUpdates = true;
        this.updateInterval = 300000; // 5 minutes
        this.charts = {};
        this.notifications = [];
        
        this.init();
    }
    
    init() {
        this.initializeRealTimeUpdates();
        this.setupEventListeners();
        this.initializeNotifications();
        console.log('Enhanced Dashboard Manager initialized');
    }
    
    initializeRealTimeUpdates() {
        if (this.realTimeUpdates) {
            setInterval(() => {
                this.refreshDashboardData();
            }, this.updateInterval);
        }
    }
    
    async refreshDashboardData() {
        try {
            // Update BTTS predictions
            if (document.getElementById('enhancedPredictionsTable')) {
                await this.refreshPredictionsTable();
            }
            
            // Update validation results
            if (document.getElementById('validationResultsTable')) {
                await this.refreshValidationResults();
            }
            
            // Update charts
            await this.refreshCharts();
            
            this.showNotification('Dashboard updated successfully', 'success', 2000);
        } catch (error) {
            console.error('Dashboard refresh error:', error);
            this.showNotification('Failed to update dashboard', 'error', 5000);
        }
    }
    
    async refreshPredictionsTable() {
        const season = this.getSelectedSeason();
        const response = await this.apiRequest(`/api/enhanced-predictions?season=${season}&limit=20`);
        
        if (response.status === 'success') {
            this.updatePredictionsTable(response.data);
        }
    }
    
    async refreshValidationResults() {
        const response = await this.apiRequest('/api/enhanced-validation-results?days=30');
        
        if (response.status === 'success') {
            this.updateValidationTable(response.data);
        }
    }
    
    async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    updatePredictionsTable(predictions) {
        const tbody = document.querySelector('#enhancedPredictionsTable tbody');
        if (!tbody) return;
        
        tbody.innerHTML = predictions.map(pred => this.renderPredictionRow(pred)).join('');
        this.addTableInteractivity();
    }
    
    renderPredictionRow(pred) {
        return `
            <tr class="prediction-row" data-match-id="${pred.match_id}">
                <td>
                    <strong>${pred.home_team_name}</strong> vs <strong>${pred.away_team_name}</strong>
                    <br><small class="text-muted">${this.formatDate(pred.match_date)}</small>
                </td>
                <td>
                    <div class="btts-display">
                        <div class="progress-circle" data-percentage="${pred.btts_probability}">
                            <span class="percentage">${pred.btts_probability.toFixed(1)}%</span>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="team-probabilities">
                        <span class="badge bg-primary">${pred.home_team_score_probability.toFixed(1)}%</span>
                        <span class="badge bg-secondary">${pred.away_team_score_probability.toFixed(1)}%</span>
                    </div>
                </td>
                <td>
                    <div class="weight-visualization">
                        <div class="weight-bar attack-weight" style="width: ${pred.attack_weight * 100}%"></div>
                        <div class="weight-bar defense-weight" style="width: ${pred.defense_weight * 100}%"></div>
                    </div>
                </td>
                <td>
                    <span class="badge quality-${pred.prediction_quality_grade.toLowerCase()}">
                        ${pred.prediction_quality_grade}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.enhancedDashboard.viewPredictionDetails(${pred.match_id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }
    
    addTableInteractivity() {
        // Add hover effects
        document.querySelectorAll('.prediction-row').forEach(row => {
            row.addEventListener('mouseenter', (e) => {
                e.target.classList.add('row-highlighted');
            });
            
            row.addEventListener('mouseleave', (e) => {
                e.target.classList.remove('row-highlighted');
            });
        });
    }
    
    viewPredictionDetails(matchId) {
        window.location.href = `/enhanced-prediction/${matchId}`;
    }
    
    setupEventListeners() {
        // Season filter changes
        document.querySelectorAll('.season-filter').forEach(filter => {
            filter.addEventListener('change', (e) => {
                this.handleSeasonChange(e.target.value);
            });
        });
        
        // Refresh buttons
        document.querySelectorAll('.refresh-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.refreshDashboardData();
            });
        });
    }
    
    handleSeasonChange(season) {
        this.activeFilters.season = season;
        this.refreshDashboardData();
    }
    
    getSelectedSeason() {
        return this.activeFilters.season || '2024';
    }
    
    formatDate(dateString) {
        if (!dateString) return 'TBD';
        return new Date(dateString).toLocaleDateString();
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        const container = this.getNotificationContainer();
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, duration);
    }
    
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    getNotificationContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    initializeNotifications() {
        // Add notification styles
        const style = document.createElement('style');
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            }
            
            .notification {
                margin-bottom: 10px;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                opacity: 0;
                transform: translateX(100%);
                animation: slideInRight 0.3s ease forwards;
            }
            
            .notification-success { background: var(--enhanced-success); color: white; }
            .notification-error { background: var(--enhanced-danger); color: white; }
            .notification-warning { background: var(--enhanced-warning); color: white; }
            .notification-info { background: var(--enhanced-info); color: white; }
            
            .notification-content {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .notification-close {
                background: none;
                border: none;
                color: inherit;
                font-size: 18px;
                cursor: pointer;
                margin-left: auto;
            }
            
            @keyframes slideInRight {
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Enhanced Chart Manager for sophisticated visualizations
 */
class EnhancedChartManager {
    constructor() {
        this.charts = new Map();
        this.chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 1000,
                easing: 'easeInOutCubic'
            }
        };
    }
    
    createConfidenceCalibrationChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const chart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Confidence vs Success Rate',
                    data: data.points,
                    backgroundColor: 'rgba(78, 115, 223, 0.6)',
                    borderColor: 'rgba(78, 115, 223, 1)',
                    pointRadius: 6
                }, {
                    label: 'Perfect Calibration',
                    data: [{x: 0, y: 0}, {x: 100, y: 100}],
                    type: 'line',
                    borderColor: 'rgba(28, 200, 138, 1)',
                    backgroundColor: 'transparent',
                    pointRadius: 0,
                    borderWidth: 2,
                    borderDash: [5, 5]
                }]
            },
            options: {
                ...this.chartOptions,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Predicted Probability (%)'
                        },
                        min: 0,
                        max: 100
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Actual Success Rate (%)'
                        },
                        min: 0,
                        max: 100
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `Predicted: ${context.parsed.x}%, Actual: ${context.parsed.y}%`;
                            }
                        }
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    createDynamicWeightChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Attack Weight', 'Defense Weight', 'Venue Analysis', 'Team Strength', 'Form Analysis', 'Historical Data'],
                datasets: [{
                    label: 'Effectiveness Score',
                    data: data.effectiveness,
                    backgroundColor: 'rgba(78, 115, 223, 0.2)',
                    borderColor: 'rgba(78, 115, 223, 1)',
                    pointBackgroundColor: 'rgba(78, 115, 223, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                ...this.chartOptions,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    createBTTSAccuracyTrend(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: 'BTTS Accuracy',
                    data: data.accuracy,
                    borderColor: 'rgba(28, 200, 138, 1)',
                    backgroundColor: 'rgba(28, 200, 138, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Confidence Score',
                    data: data.confidence,
                    borderColor: 'rgba(246, 194, 62, 1)',
                    backgroundColor: 'rgba(246, 194, 62, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...this.chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Percentage (%)'
                        }
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.data = newData;
            chart.update('active');
        }
    }
    
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    }
}

/**
 * Enhanced Prediction Detail Manager
 */
class EnhancedPredictionDetailManager {
    constructor(matchId) {
        this.matchId = matchId;
        this.predictionData = null;
        this.validationData = null;
        
        this.init();
    }
    
    async init() {
        await this.loadPredictionData();
        this.initializeComponents();
        this.setupInteractivity();
    }
    
    async loadPredictionData() {
        try {
            const response = await fetch(`/api/enhanced-predictions?match_id=${this.matchId}`);
            const data = await response.json();
            if (data.status === 'success') {
                this.predictionData = data.data;
            }
        } catch (error) {
            console.error('Failed to load prediction data:', error);
        }
    }
    
    initializeComponents() {
        this.createBTTSVisualization();
        this.createDynamicWeightVisualization();
        this.createVenueAnalysisChart();
        this.initializeProgressBars();
    }
    
    createBTTSVisualization() {
        const container = document.getElementById('btts-visualization');
        if (!container || !this.predictionData) return;
        
        const bttsProb = this.predictionData.btts_probability;
        const homeProb = this.predictionData.home_team_score_probability;
        const awayProb = this.predictionData.away_team_score_probability;
        
        container.innerHTML = `
            <div class="btts-visual-grid">
                <div class="probability-circle main-circle">
                    <div class="circle-progress" data-percentage="${bttsProb}">
                        <span class="percentage">${bttsProb.toFixed(1)}%</span>
                        <span class="label">BTTS</span>
                    </div>
                </div>
                <div class="team-circles">
                    <div class="probability-circle">
                        <div class="circle-progress home-circle" data-percentage="${homeProb}">
                            <span class="percentage">${homeProb.toFixed(1)}%</span>
                            <span class="label">Home</span>
                        </div>
                    </div>
                    <div class="probability-circle">
                        <div class="circle-progress away-circle" data-percentage="${awayProb}">
                            <span class="percentage">${awayProb.toFixed(1)}%</span>
                            <span class="label">Away</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.animateCircularProgress();
    }
    
    animateCircularProgress() {
        const circles = document.querySelectorAll('.circle-progress');
        circles.forEach(circle => {
            const percentage = parseFloat(circle.dataset.percentage);
            const circumference = 2 * Math.PI * 45; // radius 45
            const strokeDashoffset = circumference - (percentage / 100) * circumference;
            
            // Add SVG circle if not exists
            if (!circle.querySelector('svg')) {
                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.setAttribute('viewBox', '0 0 100 100');
                svg.innerHTML = `
                    <circle cx="50" cy="50" r="45" stroke="#e3e6f0" stroke-width="8" fill="none"/>
                    <circle cx="50" cy="50" r="45" stroke="currentColor" stroke-width="8" fill="none"
                            stroke-linecap="round" stroke-dasharray="${circumference}"
                            stroke-dashoffset="${circumference}" class="progress-circle"/>
                `;
                circle.appendChild(svg);
            }
            
            // Animate
            const progressCircle = circle.querySelector('.progress-circle');
            setTimeout(() => {
                progressCircle.style.strokeDashoffset = strokeDashoffset;
                progressCircle.style.transition = 'stroke-dashoffset 1s ease-in-out';
            }, 100);
        });
    }
    
    setupInteractivity() {
        // Add tooltips, hover effects, and interactive elements
        this.setupTooltips();
        this.setupModalTriggers();
        this.setupExportFunctionality();
    }
    
    setupTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', (e) => {
                this.hideTooltip();
            });
        });
    }
    
    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'enhanced-tooltip';
        tooltip.textContent = text;
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
        tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
    }
    
    hideTooltip() {
        const tooltip = document.querySelector('.enhanced-tooltip');
        if (tooltip) tooltip.remove();
    }
    
    setupModalTriggers() {
        // Add modal functionality for detailed views
    }
    
    setupExportFunctionality() {
        // Add export functionality
    }
}

/**
 * Enhanced Form Validation
 */
class EnhancedFormValidator {
    static validatePredictionInput(formData) {
        const errors = [];
        
        // Validate BTTS probability
        if (formData.btts_probability < 0 || formData.btts_probability > 100) {
            errors.push('BTTS probability must be between 0 and 100');
        }
        
        // Validate confidence score
        if (formData.confidence_score < 0 || formData.confidence_score > 100) {
            errors.push('Confidence score must be between 0 and 100');
        }
        
        // Validate weights
        if (Math.abs((formData.attack_weight + formData.defense_weight) - 1.0) > 0.01) {
            errors.push('Attack and defense weights must sum to 1.0');
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
}

/**
 * Initialize Enhanced Dashboard on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize enhanced dashboard if on dashboard page
    if (document.querySelector('.enhanced-btts-dashboard') || document.querySelector('.enhanced-accuracy-dashboard')) {
        window.enhancedDashboard = new EnhancedDashboardManager();
        window.chartManager = new EnhancedChartManager();
    }
    
    // Initialize prediction detail manager if on detail page
    const matchId = document.querySelector('[data-match-id]');
    if (matchId) {
        window.predictionDetail = new EnhancedPredictionDetailManager(matchId.dataset.matchId);
    }
    
    // Add enhanced CSS for JavaScript components
    const style = document.createElement('style');
    style.textContent = `
        .row-highlighted {
            background-color: rgba(0, 123, 255, 0.1) !important;
            transform: scale(1.01);
            transition: all 0.2s ease;
        }
        
        .btts-visual-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 2rem;
            align-items: center;
        }
        
        .probability-circle {
            position: relative;
            width: 120px;
            height: 120px;
        }
        
        .main-circle .probability-circle {
            width: 180px;
            height: 180px;
        }
        
        .circle-progress {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .circle-progress svg {
            position: absolute;
            width: 100%;
            height: 100%;
            transform: rotate(-90deg);
        }
        
        .circle-progress .percentage {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--enhanced-primary);
        }
        
        .circle-progress .label {
            font-size: 0.875rem;
            color: var(--enhanced-dark);
            margin-top: 0.25rem;
        }
        
        .home-circle { color: var(--enhanced-primary); }
        .away-circle { color: var(--enhanced-info); }
        
        .team-circles {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .enhanced-tooltip {
            position: absolute;
            background: var(--enhanced-dark);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.875rem;
            z-index: 9999;
            pointer-events: none;
            opacity: 0.95;
        }
        
        .enhanced-tooltip::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border: 5px solid transparent;
            border-top-color: var(--enhanced-dark);
        }
    `;
    document.head.appendChild(style);
});

// Export enhanced functions for global use
window.EnhancedCSLPredictions = {
    EnhancedDashboardManager,
    EnhancedChartManager,
    EnhancedPredictionDetailManager,
    EnhancedFormValidator
};
