// API Configuration for TradeWise Frontend
// Matches the logic from the old static frontend

export function getApiUrl(): string {
  if (typeof window === 'undefined') {
    // Server-side: use env variable
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  const hostname = window.location.hostname

  // Determine API URL based on current hostname
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // Local development
    return 'http://localhost:8000'
  } else if (hostname.includes('onrender.com')) {
    // Render deployment - API is on same origin
    return window.location.origin
  } else if (hostname === 'stocxer.in' || hostname.includes('stocxer')) {
    // Custom domain - API is on Render
    return 'https://stocxer-ai.onrender.com'
  } else if (hostname.includes('vercel.app')) {
    // Vercel deployment - use configured API or Render
    return process.env.NEXT_PUBLIC_API_URL || 'https://stocxer-ai.onrender.com'
  } else {
    // Fallback - assume same origin
    return window.location.origin
  }
}

export const config = {
  get apiUrl() {
    return getApiUrl()
  },
  get env() {
    if (typeof window === 'undefined') return 'server'
    const hostname = window.location.hostname
    return hostname === 'localhost' || hostname === '127.0.0.1' ? 'development' : 'production'
  },
  features: {
    mlPredictions: true,
    liveTrading: false,
    paperTrading: true,
  },
}
