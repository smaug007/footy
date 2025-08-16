/**
 * Main JavaScript file for China Super League Corner Prediction System
 */

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    updateCurrentTime();
    setInterval(updateCurrentTime, 60000); // Update every minute
    
    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    console.log('China Super League Corner Prediction System initialized');
}

/**
 * Update current time display
 */
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleString();
    }
}

/**
 * Show loading state on element
 * @param {HTMLElement} element - Element to show loading on
 */
function showLoading(element) {
    element.classList.add('loading');
    const button = element.querySelector('button[type="submit"]');
    if (button) {
        button.disabled = true;
        const originalText = button.innerHTML;
        button.setAttribute('data-original-text', originalText);
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    }
}

/**
 * Hide loading state on element
 * @param {HTMLElement} element - Element to hide loading on
 */
function hideLoading(element) {
    element.classList.remove('loading');
    const button = element.querySelector('button[type="submit"]');
    if (button) {
        button.disabled = false;
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.innerHTML = originalText;
        }
    }
}

/**
 * Show alert message
 * @param {string} message - Message to show
 * @param {string} type - Alert type (success, warning, danger, info)
 * @param {number} duration - Auto-hide duration in milliseconds (optional)
 */
function showAlert(message, type = 'info', duration = 0) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        // Create alert container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.className = 'container mt-3';
        document.querySelector('main').prepend(container);
    }
    
    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.getElementById('alert-container').insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto-hide after duration
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                alert.remove();
            }
        }, duration);
    }
}

/**
 * Make API request with error handling
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise} - Fetch promise
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showAlert(`API Error: ${error.message}`, 'danger', 5000);
        throw error;
    }
}

/**
 * Format confidence percentage with appropriate styling
 * @param {number} confidence - Confidence percentage (0-100)
 * @returns {string} - HTML string with styled confidence
 */
function formatConfidence(confidence) {
    let className = 'confidence-low';
    let icon = '⚠️';
    
    if (confidence >= 80) {
        className = 'confidence-high';
        icon = '✅';
    } else if (confidence >= 60) {
        className = 'confidence-medium';
        icon = '⚡';
    }
    
    return `<span class="${className}">${icon} ${confidence}%</span>`;
}

/**
 * Format accuracy percentage with appropriate styling
 * @param {number} accuracy - Accuracy percentage (0-100)
 * @returns {string} - HTML string with styled accuracy
 */
function formatAccuracy(accuracy) {
    let className = 'accuracy-poor';
    
    if (accuracy >= 80) {
        className = 'accuracy-excellent';
    } else if (accuracy >= 65) {
        className = 'accuracy-good';
    }
    
    return `<span class="${className}">${accuracy}%</span>`;
}

/**
 * Validate form data
 * @param {HTMLFormElement} form - Form element to validate
 * @returns {boolean} - True if valid
 */
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Debug function for development
 */
function debugLog(message, data = null) {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log(`[CSL Predictions] ${message}`, data);
    }
}

// Export functions for use in other scripts
window.CSLPredictions = {
    showLoading,
    hideLoading,
    showAlert,
    apiRequest,
    formatConfidence,
    formatAccuracy,
    validateForm,
    debugLog
};
