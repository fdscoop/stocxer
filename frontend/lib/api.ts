import { getApiUrl } from './config'

async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  const apiBase = getApiUrl()
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  }

  const response = await fetch(`${apiBase}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `API Error: ${response.statusText}`)
  }

  return response.json()
}

// Export getApiUrl for components that need direct access
export { getApiUrl }

export const api = {
  // Index Options
  async getIndexData(index: string, expiry?: string) {
    const params = new URLSearchParams({ index })
    if (expiry) params.append('expiry', expiry)
    return fetchWithAuth(`/api/index-analysis?${params}`)
  },

  async getOptionChain(index: string, expiry?: string) {
    const params = new URLSearchParams({ index })
    if (expiry) params.append('expiry', expiry)
    return fetchWithAuth(`/api/option-chain?${params}`)
  },

  async getExpiries(index: string) {
    return fetchWithAuth(`/api/expiries?index=${index}`)
  },

  // Stock Screener
  async runScreener(limit: number, minConfidence: number, action: string) {
    return fetchWithAuth('/api/screener/scan', {
      method: 'POST',
      body: JSON.stringify({ limit, min_confidence: minConfidence, action }),
    })
  },

  async getRecentScans(days: number = 7) {
    return fetchWithAuth(`/api/screener/recent?days=${days}`)
  },

  async getRecentSignals() {
    return fetchWithAuth('/api/screener/recent-signals')
  },

  // Options Scanner
  async scanOptions(index: string, expiry: string, minVolume: number, minOI: number) {
    return fetchWithAuth('/api/options-scanner', {
      method: 'POST',
      body: JSON.stringify({
        index,
        expiry,
        min_volume: minVolume,
        min_oi: minOI,
      }),
    })
  },

  // Auth
  async login(email: string, password: string) {
    return fetchWithAuth('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },

  async register(email: string, password: string, name?: string) {
    return fetchWithAuth('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    })
  },

  async checkAuth() {
    return fetchWithAuth('/api/auth/verify')
  },

  async checkFyersAuth() {
    return fetchWithAuth('/api/fyers/check-auth')
  },
}
