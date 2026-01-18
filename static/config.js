// API Configuration for TradeWise
// This file is dynamically generated during build/deployment

window.APP_CONFIG = {
    // Railway backend URL - set this during deployment
    API_URL: window.RAILWAY_API_URL || 'PLACEHOLDER_API_URL' || window.location.origin,
    
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

console.log('TradeWise Config:', {
    API_URL: window.APP_CONFIG.API_URL,
    ENV: window.APP_CONFIG.ENV
});
