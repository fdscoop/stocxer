import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://cxbcpmouqkajlxzmbomu.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4YmNwbW91cWthamx4em1ib211Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NjA3NjMsImV4cCI6MjA4NDMzNjc2M30.oBozxBnSKARn-3xkRy8ceNU3wpxXh8MBReGtmtsBpEw'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const error = requestUrl.searchParams.get('error')
  const error_description = requestUrl.searchParams.get('error_description')

  if (error) {
    console.error('Auth callback error:', error, error_description)
    return NextResponse.redirect(
      new URL(`/login?error=${encodeURIComponent(error_description || error)}`, request.url)
    )
  }

  if (code) {
    const supabase = createClient(supabaseUrl, supabaseAnonKey)
    
    try {
      const { data, error } = await supabase.auth.exchangeCodeForSession(code)
      
      if (error) throw error
      
      // Redirect to dashboard with success message
      return NextResponse.redirect(
        new URL('/login?confirmed=true&message=Email confirmed successfully! Please login.', request.url)
      )
    } catch (err) {
      console.error('Error exchanging code for session:', err)
      return NextResponse.redirect(
        new URL('/login?error=Failed to confirm email. Please try again.', request.url)
      )
    }
  }

  // No code, redirect to login
  return NextResponse.redirect(new URL('/login', request.url))
}
