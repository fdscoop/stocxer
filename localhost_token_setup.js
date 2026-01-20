// TradeWise - Localhost Token Setup
// Use this script to set authentication tokens for localhost testing

// Based on your database, your user token is:
const LOCALHOST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZjFkMWI0NC03NDU5LTQzZmEtOGFlYy1mOWI5YTA2MDVjNGIiLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJleHAiOjE3Mzc5NDcwNTcsImlhdCI6MTczNzM0MjI1N30.KK-7dDbtSGxEw5wFmdADKCx2VVGfNzOQkwFg7Sh4Fxk";

const LOCALHOST_USER = {
    id: "4f1d1b44-7459-43fa-8aec-f9b9a0605c4b",
    email: "test@test.com",
    full_name: "Test User"
};

// Function to set up localhost authentication
function setupLocalhostAuth() {
    console.log('🔧 Setting up localhost authentication...');
    
    // Clear any existing auth data
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    
    // Set the token and user data
    localStorage.setItem('auth_token', LOCALHOST_TOKEN);
    localStorage.setItem('user', JSON.stringify(LOCALHOST_USER));
    
    console.log('✅ Authentication set up successfully!');
    console.log('📱 You can now access the dashboard without login');
    console.log('🔄 Refresh the page to see the changes');
    
    return true;
}

// Function to check current auth status
function checkCurrentAuth() {
    const token = localStorage.getItem('auth_token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
        console.log('✅ Currently authenticated');
        console.log('👤 User:', JSON.parse(user).email);
        console.log('🎫 Token:', token.substring(0, 20) + '...');
        return true;
    } else {
        console.log('❌ Not authenticated');
        return false;
    }
}

// Function to clear authentication
function clearAuth() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    console.log('🗑️ Authentication cleared');
    console.log('🔄 Refresh the page to see the changes');
}

// Auto-setup for localhost development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('🏠 Localhost detected - TradeWise Token Setup Available');
    console.log('📚 Available functions:');
    console.log('  setupLocalhostAuth() - Set up authentication for localhost');
    console.log('  checkCurrentAuth() - Check current authentication status');
    console.log('  clearAuth() - Clear authentication data');
    console.log('');
    console.log('💡 Run setupLocalhostAuth() in console to authenticate instantly');
    
    // Make functions globally available
    window.setupLocalhostAuth = setupLocalhostAuth;
    window.checkCurrentAuth = checkCurrentAuth;
    window.clearAuth = clearAuth;
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        setupLocalhostAuth,
        checkCurrentAuth,
        clearAuth,
        LOCALHOST_TOKEN,
        LOCALHOST_USER
    };
}