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
  } else if (hostname === 'stocxer.in' || hostname === 'www.stocxer.in' || hostname.includes('stocxer')) {
    // Production - use Google Cloud Run backend
    return 'https://stocxer-484044910258.europe-west1.run.app'
  } else if (hostname.includes('vercel.app')) {
    // Vercel deployment - use Google Cloud Run
    return process.env.NEXT_PUBLIC_API_URL || 'https://stocxer-484044910258.europe-west1.run.app'
  } else if (hostname.includes('onrender.com')) {
    // Old Render deployment fallback
    return 'https://stocxer-484044910258.europe-west1.run.app'
  } else {
    // Fallback - use Google Cloud Run
    return 'https://stocxer-484044910258.europe-west1.run.app'
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
