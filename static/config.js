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
    const isApiCall = urlStr.includes(window.APP_CONFIG.API_URL) ||
                      urlStr.includes('ngrok') ||
                      urlStr.startsWith(window.APP_CONFIG.API_URL);

    if (isApiCall) {
        options.headers = {
            'ngrok-skip-browser-warning': 'true',
            ...(options.headers || {})
        };
    }
    return originalFetch(url, options);
};

console.log('TradeWise Config:', {
    API_URL: window.APP_CONFIG.API_URL,
    ENV: window.APP_CONFIG.ENV
});
