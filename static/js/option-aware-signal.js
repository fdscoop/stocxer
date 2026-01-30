/**
 * Option-Aware ICT Signal Integration for Dashboard
 * Fetches and displays specific option strikes with premium targets
 */

// Global state
let optionAwareSignal = null;
let autoRefreshInterval = null;

/**
 * Fetch option-aware signal from backend
 */
async function fetchOptionAwareSignal(index) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            console.error('No auth token found');
            return null;
        }

        const response = await fetch(`/api/signals/${index}/option-aware`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            console.error('Failed to fetch option-aware signal:', error);
            return null;
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching option-aware signal:', error);
        return null;
    }
}

/**
 * Display option-aware signal in the dashboard card
 */
function displayOptionAwareSignal(data) {
    if (!data || !data.signal) {
        document.getElementById('option-aware-card').style.display = 'none';
        return;
    }

    const signal = data.signal;
    const card = document.getElementById('option-aware-card');
    card.style.display = 'block';

    // Update timestamp
    document.getElementById('oa-timestamp').textContent = new Date(data.timestamp).toLocaleTimeString();

    // Handle WAIT signal
    if (signal.signal === 'WAIT') {
        document.getElementById('oa-signal-type').textContent = 'WAIT';
        document.getElementById('oa-signal-badge').className = 'text-xs bg-yellow-600 px-2 py-1 rounded';
        document.getElementById('oa-wait-message').style.display = 'block';
        document.getElementById('oa-signal-details').style.display = 'none';
        document.getElementById('oa-wait-reason').textContent = signal.reasoning ? signal.reasoning[0] : 'No setup found';
        return;
    }

    // Show signal details
    document.getElementById('oa-wait-message').style.display = 'none';
    document.getElementById('oa-signal-details').style.display = 'block';

    // Update signal header
    document.getElementById('oa-signal-type').textContent = signal.action;
    document.getElementById('oa-signal-badge').className = signal.action.includes('BUY') ?
        'text-xs bg-green-600 px-2 py-1 rounded' : 'text-xs bg-red-600 px-2 py-1 rounded';

    // Update confidence
    const conf = signal.confidence;
    document.getElementById('oa-confidence').textContent = `${conf.score}%`;
    document.getElementById('oa-confidence-level').textContent = conf.level;

    // Color code confidence
    const confElement = document.getElementById('oa-confidence');
    if (conf.score >= 75) {
        confElement.className = 'text-2xl font-bold text-green-400';
    } else if (conf.score >= 60) {
        confElement.className = 'text-2xl font-bold text-yellow-400';
    } else {
        confElement.className = 'text-2xl font-bold text-orange-400';
    }

    // Update tier
    document.getElementById('oa-tier').textContent = `Tier ${signal.tier}`;
    document.getElementById('oa-setup-type').textContent = signal.setup_type;

    // Update option details
    const opt = signal.option;
    document.getElementById('oa-strike').textContent = `${opt.strike} ${opt.type}`;
    document.getElementById('oa-entry-price').textContent = `₹${opt.entry_price.toFixed(2)}`;
    document.getElementById('oa-symbol').textContent = opt.symbol;
    document.getElementById('oa-delta').textContent = opt.delta.toFixed(3);
    document.getElementById('oa-gamma').textContent = opt.gamma ? opt.gamma.toFixed(4) : 'N/A';
    document.getElementById('oa-theta').textContent = opt.theta ? opt.theta.toFixed(2) : 'N/A';
    document.getElementById('oa-iv').textContent = opt.iv ? `${opt.iv.toFixed(1)}%` : 'N/A';
    document.getElementById('oa-volume').textContent = opt.volume.toLocaleString();
    document.getElementById('oa-oi').textContent = opt.oi.toLocaleString();

    // Update targets
    const targets = signal.targets;
    document.getElementById('oa-target1').textContent = `₹${targets.target_1_price.toFixed(2)} (+${targets.target_1_points.toFixed(1)} pts)`;
    document.getElementById('oa-target2').textContent = `₹${targets.target_2_price.toFixed(2)} (+${targets.target_2_points.toFixed(1)} pts)`;
    document.getElementById('oa-stoploss').textContent = `₹${targets.stop_loss_price.toFixed(2)} (-${targets.stop_loss_points.toFixed(1)} pts)`;

    // Update risk/reward
    const rr = signal.risk_reward;
    document.getElementById('oa-risk').textContent = `₹${rr.risk_per_lot.toLocaleString()}`;
    document.getElementById('oa-reward1').textContent = `₹${rr.reward_1_per_lot.toLocaleString()} (${rr.ratio_1})`;
    document.getElementById('oa-reward2').textContent = `₹${rr.reward_2_per_lot.toLocaleString()} (${rr.ratio_2})`;
    document.getElementById('oa-lot-size').textContent = signal.lot_size;

    // Update index context
    const ctx = signal.index_context;
    document.getElementById('oa-spot-price').textContent = `₹${ctx.spot_price.toLocaleString()}`;
    document.getElementById('oa-expected-move').textContent = `${ctx.expected_move} points`;

    // Show notification for high confidence signals
    if (conf.score >= 75 && Notification.permission === 'granted') {
        new Notification('TradeWise: High Confidence Signal!', {
            body: `${signal.action}: ${opt.strike} ${opt.type} @ ₹${opt.entry_price.toFixed(2)} (${conf.score}% confidence)`,
            icon: '/static/icon-192.png',
            tag: 'option-aware-signal'
        });
    }

    // Store signal globally
    optionAwareSignal = data;
}

/**
 * Refresh option-aware signal for current index
 */
async function refreshOptionAwareSignal() {
    const currentIndex = getCurrentIndex(); // This function should exist in main JS
    const refreshBtn = document.getElementById('oa-refresh-btn');

    if (refreshBtn) {
        refreshBtn.innerHTML = '<i data-lucide="loader" class="w-4 h-4 animate-spin"></i>';
        lucide.createIcons();
    }

    const data = await fetchOptionAwareSignal(currentIndex);
    displayOptionAwareSignal(data);

    if (refreshBtn) {
        refreshBtn.innerHTML = '<i data-lucide="refresh-cw" class="w-4 h-4"></i>';
        lucide.createIcons();
    }
}

/**
 * Start auto-refresh (every 2 minutes during market hours)
 */
function startOptionAwareAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }

    // Refresh every 2 minutes
    autoRefreshInterval = setInterval(async () => {
        await refreshOptionAwareSignal();
    }, 120000); // 2 minutes
}

/**
 * Stop auto-refresh
 */
function stopOptionAwareAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

/**
 * Request notification permission
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    requestNotificationPermission();

    // Initial load
    setTimeout(() => {
        refreshOptionAwareSignal();
        st

        artOptionAwareAutoRefresh();
    }, 2000); // Wait 2s after page load
});
