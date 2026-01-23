import { getApiUrl } from './config'

// Helper to get token from any possible key (for backward compatibility)
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null

  // Try all possible keys (for backward compatibility)
  return localStorage.getItem('auth_token') ||
    localStorage.getItem('token') ||
    localStorage.getItem('jwt_token')
}

// Helper to set token consistently
export function setAuthToken(token: string) {
  if (typeof window === 'undefined') return

  // Store in primary key
  localStorage.setItem('auth_token', token)

  // Remove old keys for consistency
  localStorage.removeItem('token')
  localStorage.removeItem('jwt_token')
}

// Helper to clear all auth data
export function clearAuthData() {
  if (typeof window === 'undefined') return

  localStorage.removeItem('auth_token')
  localStorage.removeItem('token')
  localStorage.removeItem('jwt_token')
  localStorage.removeItem('user')
  localStorage.removeItem('userEmail')
}

async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken()
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

  // ✅ Handle 401 errors - token expired or invalid
  if (response.status === 401) {
    console.warn('⚠️ Session expired (401) - clearing auth data and redirecting to login')

    // Clear invalid token
    clearAuthData()

    // Redirect to login (avoid infinite loop)
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = '/login?expired=true'
    }

    throw new Error('Session expired. Please login again.')
  }

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
