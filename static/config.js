// API Configuration for TradeWise
// This file is dynamically generated during build/deployment

window.APP_CONFIG = {
    // ngrok backend URL
    API_URL: 'https://7ba080a7b86b.ngrok-free.app',

    // Environment
    ENV: 'production',

    // Feature flags
    FEATURES: {
        ML_PREDICTIONS: false, // Disabled in frontend-only deployment
        LIVE_TRADING: false,
        PAPER_TRADING: true
    }
};

// Set global API base URL
window.API_BASE = window.APP_CONFIG.API_URL;

// Override fetch to add ngrok header automatically for all API calls
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    const urlStr = url.toString();
    const isApiCall = urlStr.includes('ngrok') ||
                      urlStr.includes(window.APP_CONFIG.API_URL);

    if (isApiCall) {
        // Ensure headers object exists and add ngrok header
        if (!options.headers) {
            options.headers = {};
        }

        // Handle both Headers object and plain object
        if (options.headers instanceof Headers) {
            options.headers.set('ngrok-skip-browser-warning', 'true');
        } else {
            options.headers['ngrok-skip-browser-warning'] = 'true';
        }

        console.log('Adding ngrok header to:', urlStr.substring(0, 60) + '...');
    }
    return originalFetch.call(window, url, options);
};

console.log('TradeWise Config:', {
    API_URL: window.APP_CONFIG.API_URL,
    ENV: window.APP_CONFIG.ENV
});
