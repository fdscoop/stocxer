/**
 * API Client with automatic token refresh
 */
import { getApiUrl } from './config'

interface FetchOptions extends RequestInit {
  skipAuth?: boolean
}

/**
 * Refresh the access token using the refresh token
 */
async function refreshAccessToken(): Promise<string | null> {
  try {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      console.warn('No refresh token found')
      return null
    }

    const apiUrl = getApiUrl()
    // Send refresh token as query parameter (backend expects it this way)
    const response = await fetch(`${apiUrl}/api/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })

    if (!response.ok) {
      // Refresh token is invalid, clear all tokens
      console.warn(`Token refresh failed with status ${response.status}`)
      localStorage.removeItem('token')
      localStorage.removeItem('auth_token')
      localStorage.removeItem('jwt_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('token_expires_at')
      return null
    }

    const data = await response.json()
    
    if (data.access_token) {
      console.log('✅ Token refreshed successfully')
      // Store new tokens
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('jwt_token', data.access_token)
      
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token)
      }
      
      if (data.expires_at) {
        localStorage.setItem('token_expires_at', data.expires_at)
      }
      
      return data.access_token
    }

    console.warn('No access_token in refresh response')
    return null
  } catch (error) {
    console.error('Error refreshing token:', error)
    return null
  }
}

/**
 * Check if token is about to expire (within 5 minutes)
 */
function isTokenExpiringSoon(): boolean {
  const expiresAt = localStorage.getItem('token_expires_at')
  if (!expiresAt) return false

  const expiryTime = new Date(expiresAt).getTime()
  const now = Date.now()
  const fiveMinutes = 5 * 60 * 1000

  return (expiryTime - now) < fiveMinutes
}

/**
 * Enhanced fetch with automatic token refresh and retry
 */
export async function apiFetch(url: string, options: FetchOptions = {}): Promise<Response> {
  const { skipAuth, ...fetchOptions } = options

  // Get token
  let token = localStorage.getItem('auth_token') || 
              localStorage.getItem('token') || 
              localStorage.getItem('jwt_token')

  // Check if token is expiring soon and refresh proactively
  if (token && !skipAuth && isTokenExpiringSoon()) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      token = newToken
    }
  }

  // Add authorization header if not skipping auth
  if (token && !skipAuth) {
    fetchOptions.headers = {
      ...fetchOptions.headers,
      'Authorization': `Bearer ${token}`
    }
  }

  // Make the request
  let response = await fetch(url, fetchOptions)

  // If 401 Unauthorized, try to refresh token and retry once
  if (response.status === 401 && !skipAuth && !options.skipAuth) {
    console.log('Token expired, attempting refresh...')
    const newToken = await refreshAccessToken()
    
    if (newToken) {
      // Retry with new token
      fetchOptions.headers = {
        ...fetchOptions.headers,
        'Authorization': `Bearer ${newToken}`
      }
      response = await fetch(url, fetchOptions)
    } else {
      // Refresh failed, redirect to login
      console.error('Token refresh failed, redirecting to login')
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname)
    }
  }

  return response
}

/**
 * Helper for GET requests
 */
export async function apiGet(url: string, options: FetchOptions = {}): Promise<Response> {
  return apiFetch(url, { ...options, method: 'GET' })
}

/**
 * Helper for POST requests
 */
export async function apiPost(url: string, data?: any, options: FetchOptions = {}): Promise<Response> {
  return apiFetch(url, {
    ...options,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    body: data ? JSON.stringify(data) : undefined
  })
}

/**
 * Helper for DELETE requests
 */
export async function apiDelete(url: string, options: FetchOptions = {}): Promise<Response> {
  return apiFetch(url, { ...options, method: 'DELETE' })
}
