// API Configuration for TradeWise
// Auto-detects environment and sets appropriate API URL

(function() {
    const hostname = window.location.hostname;

    // Determine API URL based on current hostname
    let apiUrl;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        // Local development
        apiUrl = 'http://localhost:8000';
    } else if (hostname.includes('onrender.com')) {
        // Render deployment - API is on same origin
        apiUrl = window.location.origin;
    } else if (hostname === 'stocxer.in' || hostname.includes('stocxer')) {
        // Custom domain pointing to Render
        apiUrl = window.location.origin;
    } else {
        // Fallback - assume same origin
        apiUrl = window.location.origin;
    }

    window.APP_CONFIG = {
        API_URL: apiUrl,
        ENV: hostname === 'localhost' ? 'development' : 'production',
        FEATURES: {
            ML_PREDICTIONS: true,
            LIVE_TRADING: false,
            PAPER_TRADING: true
        }
    };

    // Set global API base URL
    window.API_BASE = window.APP_CONFIG.API_URL;

    console.log('TradeWise Config:', {
        API_URL: window.APP_CONFIG.API_URL,
        ENV: window.APP_CONFIG.ENV,
        hostname: hostname
    });
})();
