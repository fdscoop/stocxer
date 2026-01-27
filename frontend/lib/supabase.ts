import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://cxbcpmouqkajlxzmbomu.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4YmNwbW91cWthamx4em1ib211Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NjA3NjMsImV4cCI6MjA4NDMzNjc2M30.oBozxBnSKARn-3xkRy8ceNU3wpxXh8MBReGtmtsBpEw'

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storage: typeof window !== 'undefined' ? window.localStorage : undefined,
    // Don't expire session on inactivity - only check daily at 7 AM IST
    storageKey: 'stocxer-auth-token',
  },
})

export type User = {
  id: string
  email: string
}

export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

export async function getUser(): Promise<User | null> {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return null
  return {
    id: user.id,
    email: user.email || '',
  }
}

export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  
  // Record login time for daily session check
  if (data?.session) {
    updateLastLoginTime()
  }
  
  return { data, error }
}

export async function signUp(email: string, password: string, name?: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: name,
      },
    },
  })
  return { data, error }
}

export async function signOut() {
  const { error } = await supabase.auth.signOut()
  return { error }
}

/**
 * Check if user should be logged out based on daily 7 AM IST reset
 * Call this on app initialization
 */
export function checkDailySessionReset(): boolean {
  if (typeof window === 'undefined') return false
  
  const lastLoginKey = 'stocxer-last-login-date'
  const lastLogin = localStorage.getItem(lastLoginKey)
  
  // Get current time in IST
  const now = new Date()
  const istOffset = 5.5 * 60 * 60 * 1000 // IST is UTC+5:30
  const istTime = new Date(now.getTime() + istOffset)
  
  // Get today's 7 AM IST as Unix timestamp
  const today7AM = new Date(istTime)
  today7AM.setHours(7, 0, 0, 0)
  
  if (!lastLogin) {
    // First time - store current date
    localStorage.setItem(lastLoginKey, istTime.toISOString())
    return false
  }
  
  const lastLoginDate = new Date(lastLogin)
  
  // If last login was before today's 7 AM and now is after 7 AM, require re-login
  if (lastLoginDate < today7AM && istTime >= today7AM) {
    // Time to logout
    localStorage.removeItem(lastLoginKey)
    return true
  }
  
  return false
}

/**
 * Update the last login timestamp (call after successful login)
 */
export function updateLastLoginTime() {
  if (typeof window === 'undefined') return
  
  const now = new Date()
  const istOffset = 5.5 * 60 * 60 * 1000
  const istTime = new Date(now.getTime() + istOffset)
  
  localStorage.setItem('stocxer-last-login-date', istTime.toISOString())
}
