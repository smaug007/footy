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
 * Show loading state on element with enhanced options
 * @param {HTMLElement} element - Element to show loading on
 * @param {Object} options - Loading options
 */
function showLoading(element, options = {}) {
    const {
        overlay = false,
        skeleton = false,
        message = 'Loading...',
        dark = false
    } = options;

    element.classList.add('loading');
    
    if (overlay) {
        showLoadingOverlay(element, message, dark);
    } else if (skeleton) {
        showSkeletonLoading(element);
    } else {
        // Default button loading
        const button = element.querySelector('button[type="submit"]');
        if (button) {
            button.disabled = true;
            button.classList.add('btn-loading');
            const textSpan = button.querySelector('.btn-text') || button;
            if (!button.querySelector('.btn-text')) {
                button.innerHTML = `<span class="btn-text">${button.innerHTML}</span>`;
            }
        }
    }
}

/**
 * Hide loading state on element
 * @param {HTMLElement} element - Element to hide loading on
 */
function hideLoading(element) {
    element.classList.remove('loading');
    
    // Remove overlay
    const overlay = element.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
    
    // Remove skeleton
    element.querySelectorAll('.skeleton').forEach(skeleton => {
        skeleton.classList.remove('skeleton');
    });
    
    // Reset button
    const button = element.querySelector('button[type="submit"]');
    if (button) {
        button.disabled = false;
        button.classList.remove('btn-loading');
        const textSpan = button.querySelector('.btn-text');
        if (textSpan) {
            button.innerHTML = textSpan.innerHTML;
        }
    }
}

/**
 * Show loading overlay
 * @param {HTMLElement} element - Element to show overlay on
 * @param {string} message - Loading message
 * @param {boolean} dark - Use dark overlay
 */
function showLoadingOverlay(element, message = 'Loading...', dark = false) {
    // Make element relative for absolute positioning
    if (getComputedStyle(element).position === 'static') {
        element.style.position = 'relative';
    }
    
    const overlay = document.createElement('div');
    overlay.className = `loading-overlay ${dark ? 'dark' : ''}`;
    overlay.innerHTML = `
        <div class="text-center">
            <div class="spinner-border ${dark ? 'text-light' : 'text-primary'}" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="mt-2"><small>${message}</small></div>
        </div>
    `;
    
    element.appendChild(overlay);
}

/**
 * Show skeleton loading
 * @param {HTMLElement} element - Element to show skeleton in
 */
function showSkeletonLoading(element) {
    const skeletonHTML = `
        <div class="skeleton skeleton-text wide"></div>
        <div class="skeleton skeleton-text medium"></div>
        <div class="skeleton skeleton-text narrow"></div>
        <div class="skeleton skeleton-text wide"></div>
    `;
    
    element.innerHTML = skeletonHTML;
}

/**
 * Show progress steps
 * @param {HTMLElement} container - Container element
 * @param {Array} steps - Array of step objects
 * @param {number} currentStep - Current step index
 */
function showProgressSteps(container, steps, currentStep = 0) {
    const progressHTML = `
        <div class="progress-steps">
            ${steps.map((step, index) => `
                <div class="progress-step ${index < currentStep ? 'completed' : index === currentStep ? 'active' : ''}">
                    <div class="progress-step-circle">
                        ${index < currentStep ? '✓' : index + 1}
                    </div>
                    <div class="progress-step-label">
                        <small>${step}</small>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = progressHTML;
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
 * Comprehensive form validation with enhanced features
 * @param {HTMLFormElement} form - Form element to validate
 * @param {Object} options - Validation options
 * @returns {Object} - Validation result with details
 */
function validateForm(form, options = {}) {
    const {
        showErrors = true,
        scrollToError = true,
        customRules = {}
    } = options;
    
    const inputs = form.querySelectorAll('input, select, textarea');
    const errors = [];
    let isValid = true;
    let firstErrorElement = null;
    
    inputs.forEach(input => {
        const fieldErrors = validateField(input, customRules);
        
        if (fieldErrors.length > 0) {
            isValid = false;
            errors.push({
                field: input.name || input.id,
                element: input,
                errors: fieldErrors
            });
            
            if (!firstErrorElement) {
                firstErrorElement = input;
            }
            
            if (showErrors) {
                showFieldErrors(input, fieldErrors);
            }
        } else {
            clearFieldErrors(input);
        }
    });
    
    // Scroll to first error
    if (!isValid && scrollToError && firstErrorElement) {
        firstErrorElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
        firstErrorElement.focus();
    }
    
    return {
        isValid,
        errors,
        firstError: firstErrorElement
    };
}

/**
 * Validate individual field
 * @param {HTMLElement} input - Input element to validate
 * @param {Object} customRules - Custom validation rules
 * @returns {Array} - Array of error messages
 */
function validateField(input, customRules = {}) {
    const errors = [];
    const value = input.value.trim();
    const type = input.type;
    const required = input.hasAttribute('required');
    
    // Required validation
    if (required && !value) {
        errors.push(`${getFieldLabel(input)} is required`);
        return errors; // Don't check other rules if empty and required
    }
    
    // Skip other validations if empty and not required
    if (!value && !required) {
        return errors;
    }
    
    // Type-specific validation
    switch (type) {
        case 'email':
            if (!isValidEmail(value)) {
                errors.push('Please enter a valid email address');
            }
            break;
            
        case 'number':
            const min = input.getAttribute('min');
            const max = input.getAttribute('max');
            const numValue = parseFloat(value);
            
            if (isNaN(numValue)) {
                errors.push('Please enter a valid number');
            } else {
                if (min !== null && numValue < parseFloat(min)) {
                    errors.push(`Value must be at least ${min}`);
                }
                if (max !== null && numValue > parseFloat(max)) {
                    errors.push(`Value must be no more than ${max}`);
                }
            }
            break;
            
        case 'tel':
            if (!isValidPhone(value)) {
                errors.push('Please enter a valid phone number');
            }
            break;
    }
    
    // Length validation
    const minLength = input.getAttribute('minlength');
    const maxLength = input.getAttribute('maxlength');
    
    if (minLength && value.length < parseInt(minLength)) {
        errors.push(`Must be at least ${minLength} characters long`);
    }
    
    if (maxLength && value.length > parseInt(maxLength)) {
        errors.push(`Must be no more than ${maxLength} characters long`);
    }
    
    // Pattern validation
    const pattern = input.getAttribute('pattern');
    if (pattern && !new RegExp(pattern).test(value)) {
        errors.push('Please enter a valid format');
    }
    
    // Custom validation rules
    const fieldName = input.name || input.id;
    if (customRules[fieldName]) {
        const customError = customRules[fieldName](value, input);
        if (customError) {
            errors.push(customError);
        }
    }
    
    // Specific validation for prediction form
    if (input.id === 'home-team-select' || input.id === 'away-team-select') {
        const homeTeam = document.getElementById('home-team-select')?.value;
        const awayTeam = document.getElementById('away-team-select')?.value;
        
        if (homeTeam && awayTeam && homeTeam === awayTeam) {
            errors.push('Home and away teams must be different');
        }
    }
    
    return errors;
}

/**
 * Show field validation errors
 * @param {HTMLElement} input - Input element
 * @param {Array} errors - Array of error messages
 */
function showFieldErrors(input, errors) {
    input.classList.add('is-invalid');
    
    // Remove existing error messages
    const existingFeedback = input.parentNode.querySelector('.invalid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Add new error message
    if (errors.length > 0) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.innerHTML = errors.join('<br>');
        input.parentNode.appendChild(feedback);
    }
}

/**
 * Clear field validation errors
 * @param {HTMLElement} input - Input element
 */
function clearFieldErrors(input) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    
    const feedback = input.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

/**
 * Get field label for error messages
 * @param {HTMLElement} input - Input element
 * @returns {string} - Field label
 */
function getFieldLabel(input) {
    const label = document.querySelector(`label[for="${input.id}"]`);
    if (label) {
        return label.textContent.replace('*', '').trim();
    }
    
    return input.name || input.id || 'This field';
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if valid
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate phone format
 * @param {string} phone - Phone to validate
 * @returns {boolean} - True if valid
 */
function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
}

/**
 * Real-time validation setup
 * @param {HTMLFormElement} form - Form to setup validation for
 * @param {Object} options - Validation options
 */
function setupRealTimeValidation(form, options = {}) {
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        // Validate on blur
        input.addEventListener('blur', () => {
            const errors = validateField(input, options.customRules || {});
            if (errors.length > 0) {
                showFieldErrors(input, errors);
            } else {
                clearFieldErrors(input);
            }
        });
        
        // Clear errors on input
        input.addEventListener('input', () => {
            if (input.classList.contains('is-invalid')) {
                clearFieldErrors(input);
            }
        });
    });
}

/**
 * Debug function for development
 */
function debugLog(message, data = null) {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log(`[CSL Predictions] ${message}`, data);
    }
}

/**
 * Show accuracy warning based on team difficulty
 * @param {Object} teamData - Team data with accuracy information
 * @param {HTMLElement} container - Container to show warning in
 */
function showAccuracyWarning(teamData, container) {
    const { accuracy, difficulty, predictions_count } = teamData;
    
    let warningLevel = 'info';
    let warningMessage = '';
    let warningIcon = 'fa-info-circle';
    
    if (accuracy < 60) {
        warningLevel = 'danger';
        warningIcon = 'fa-exclamation-triangle';
        warningMessage = `⚠️ Low Accuracy Warning: We are only ${accuracy.toFixed(1)}% accurate when predicting this team's matches. Consider this when making betting decisions.`;
    } else if (accuracy < 75) {
        warningLevel = 'warning';
        warningIcon = 'fa-exclamation-circle';
        warningMessage = `⚡ Moderate Accuracy: We are ${accuracy.toFixed(1)}% accurate with this team. Predictions have moderate reliability.`;
    } else if (difficulty === 'hard') {
        warningLevel = 'warning';
        warningIcon = 'fa-chart-line';
        warningMessage = `🔍 Difficult Team: This team is historically difficult to predict accurately. Exercise caution with high-stakes bets.`;
    } else if (predictions_count < 5) {
        warningLevel = 'info';
        warningIcon = 'fa-database';
        warningMessage = `📊 Limited Data: Only ${predictions_count} predictions available for this team. Accuracy may improve with more data.`;
    }
    
    if (warningMessage) {
        const warningHTML = `
            <div class="alert alert-${warningLevel} alert-dismissible fade show mt-3" role="alert">
                <i class="fas ${warningIcon}"></i>
                <strong>Accuracy Notice:</strong> ${warningMessage}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', warningHTML);
    }
}

/**
 * Enhanced error message display with context
 * @param {string} error - Error message
 * @param {string} context - Error context
 * @param {HTMLElement} container - Container to show error in
 */
function showEnhancedError(error, context, container) {
    const errorId = 'error-' + Date.now();
    const suggestions = getErrorSuggestions(error, context);
    
    const errorHTML = `
        <div id="${errorId}" class="alert alert-danger alert-dismissible fade show" role="alert">
            <div class="d-flex">
                <div class="me-3">
                    <i class="fas fa-exclamation-triangle fa-2x"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="alert-heading">Error in ${context}</h6>
                    <p class="mb-2">${error}</p>
                    ${suggestions ? `
                        <hr>
                        <div class="mb-0">
                            <strong>Suggestions:</strong>
                            <ul class="mb-0 mt-1">
                                ${suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', errorHTML);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        const errorElement = document.getElementById(errorId);
        if (errorElement) {
            errorElement.remove();
        }
    }, 10000);
}

/**
 * Get error suggestions based on error type
 * @param {string} error - Error message
 * @param {string} context - Error context
 * @returns {Array} - Array of suggestions
 */
function getErrorSuggestions(error, context) {
    const suggestions = [];
    
    if (error.includes('network') || error.includes('fetch')) {
        suggestions.push('Check your internet connection');
        suggestions.push('Try refreshing the page');
        suggestions.push('Contact support if the problem persists');
    } else if (error.includes('validation') || error.includes('required')) {
        suggestions.push('Check all required fields are filled');
        suggestions.push('Ensure data formats are correct');
        suggestions.push('Verify team selections are different');
    } else if (error.includes('insufficient data')) {
        suggestions.push('Try selecting different teams with more historical data');
        suggestions.push('Check if teams have played enough matches this season');
        suggestions.push('Consider using teams from previous seasons');
    } else if (context.includes('prediction')) {
        suggestions.push('Try selecting different teams');
        suggestions.push('Check if the API service is available');
        suggestions.push('Refresh the page and try again');
    } else if (context.includes('verification')) {
        suggestions.push('Ensure corner counts are valid numbers');
        suggestions.push('Check if the match ID exists');
        suggestions.push('Verify the match has been played');
    }
    
    return suggestions.length > 0 ? suggestions : null;
}

/**
 * Show team difficulty indicator
 * @param {Object} teamStats - Team statistics
 * @param {HTMLElement} container - Container to show indicator in
 */
function showTeamDifficultyIndicator(teamStats, container) {
    const { consistency, accuracy, predictions_count } = teamStats;
    
    let difficulty = 'medium';
    let color = 'warning';
    let icon = 'fa-meh';
    let description = 'Moderate difficulty';
    
    if (consistency > 80 && accuracy > 75 && predictions_count > 10) {
        difficulty = 'easy';
        color = 'success';
        icon = 'fa-smile';
        description = 'Easy to predict';
    } else if (consistency < 60 || accuracy < 60 || predictions_count < 5) {
        difficulty = 'hard';
        color = 'danger';
        icon = 'fa-frown';
        description = 'Difficult to predict';
    }
    
    const indicatorHTML = `
        <div class="difficulty-indicator mb-2">
            <span class="badge bg-${color}">
                <i class="fas ${icon}"></i> ${description}
            </span>
            <small class="text-muted ms-2">
                ${consistency.toFixed(1)}% consistency, ${predictions_count} predictions
            </small>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', indicatorHTML);
}

/**
 * Progressive loading with steps
 * @param {HTMLElement} container - Container element
 * @param {Array} steps - Array of step descriptions
 * @param {Function} onComplete - Callback when complete
 */
async function progressiveLoading(container, steps, onComplete) {
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progressive-loading';
    container.appendChild(progressContainer);
    
    showProgressSteps(progressContainer, steps, 0);
    
    for (let i = 0; i < steps.length; i++) {
        showProgressSteps(progressContainer, steps, i);
        
        // Simulate step processing
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        showProgressSteps(progressContainer, steps, i + 1);
    }
    
    setTimeout(() => {
        progressContainer.remove();
        if (onComplete) onComplete();
    }, 500);
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
    debugLog,
    showAccuracyWarning,
    showEnhancedError,
    showTeamDifficultyIndicator,
    progressiveLoading,
    showProgressSteps
};
