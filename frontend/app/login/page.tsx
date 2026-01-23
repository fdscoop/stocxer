'use client'

import * as React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Cpu, Loader2, ArrowLeft } from 'lucide-react'
import { getApiUrl } from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const [loading, setLoading] = React.useState(false)
  const [message, setMessage] = React.useState<{ text: string; isError: boolean } | null>(null)

  // Login form
  const [loginEmail, setLoginEmail] = React.useState('')
  const [loginPassword, setLoginPassword] = React.useState('')

  // Register form
  const [registerName, setRegisterName] = React.useState('')
  const [registerEmail, setRegisterEmail] = React.useState('')
  const [registerPassword, setRegisterPassword] = React.useState('')
  const [confirmPassword, setConfirmPassword] = React.useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      const apiUrl = getApiUrl()
      const response = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      })

      const data = await response.json()

      if (response.ok && data.access_token) {
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('jwt_token', data.access_token)
        localStorage.setItem('auth_token', data.access_token) // For compatibility with old frontend
        localStorage.setItem('userEmail', loginEmail)
        
        // Check if there's a pending Fyers auth code to process
        const urlParams = new URLSearchParams(window.location.search)
        const fyersAuthCode = urlParams.get('fyers_auth_code')
        const state = urlParams.get('state')
        
        if (fyersAuthCode) {
          setMessage({ text: 'Login successful! Processing Fyers authentication...', isError: false })
          
          try {
            // Process the Fyers authentication
            const fyersResponse = await fetch(`${apiUrl}/auth/callback`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${data.access_token}`
              },
              body: JSON.stringify({
                auth_code: fyersAuthCode,
                state: state
              })
            })
            
            const fyersData = await fyersResponse.json()
            
            if (fyersResponse.ok) {
              setMessage({ text: 'Login and Fyers authentication successful! Redirecting...', isError: false })
              setTimeout(() => router.push('/'), 2000)
            } else {
              setMessage({ text: 'Login successful, but Fyers auth failed. You can try connecting again from dashboard.', isError: false })
              setTimeout(() => router.push('/'), 3000)
            }
          } catch (fyersError) {
            setMessage({ text: 'Login successful, but Fyers auth failed. You can try connecting again from dashboard.', isError: false })
            setTimeout(() => router.push('/'), 3000)
          }
        } else {
          setMessage({ text: 'Login successful! Redirecting...', isError: false })
          setTimeout(() => router.push('/'), 1000)
        }
      } else {
        setMessage({ text: data.detail || 'Login failed', isError: true })
      }
    } catch (error) {
      setMessage({ text: 'Network error. Please try again.', isError: true })
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    if (registerPassword !== confirmPassword) {
      setMessage({ text: 'Passwords do not match', isError: true })
      setLoading(false)
      return
    }

    try {
      const apiUrl = getApiUrl()
      const response = await fetch(`${apiUrl}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: registerEmail,
          password: registerPassword,
          name: registerName,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setMessage({ text: 'Account created! Please login.', isError: false })
      } else {
        setMessage({ text: data.detail || 'Registration failed', isError: true })
      }
    } catch (error) {
      setMessage({ text: 'Network error. Please try again.', isError: true })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-primary/20 via-background to-purple-900/20">
      <div className="w-full max-w-md">
        {/* Back to Landing */}
        <Link
          href="/landing"
          className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>

        {/* Logo/Header */}
        <div className="text-center mb-6 md:mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-10 h-10 md:w-12 md:h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl flex items-center justify-center">
              <Cpu className="w-6 h-6 md:w-7 md:h-7 text-white" />
            </div>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold">Stocxer AI</h1>
          <p className="text-muted-foreground text-sm md:text-base">Powered by Watchman AI v3.5</p>
        </div>

        {/* Login/Register Card */}
        <Card className="border-border/50 shadow-2xl">
          <CardHeader className="pb-2">
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Login</TabsTrigger>
                <TabsTrigger value="register">Register</TabsTrigger>
              </TabsList>

              <TabsContent value="login" className="mt-4">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email">Email</Label>
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="your@email.com"
                      value={loginEmail}
                      onChange={(e) => setLoginEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password">Password</Label>
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="••••••••"
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Login
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="mt-4">
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-name">Full Name</Label>
                    <Input
                      id="register-name"
                      type="text"
                      placeholder="John Doe"
                      value={registerName}
                      onChange={(e) => setRegisterName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-email">Email</Label>
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="your@email.com"
                      value={registerEmail}
                      onChange={(e) => setRegisterEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password">Password</Label>
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="••••••••"
                      value={registerPassword}
                      onChange={(e) => setRegisterPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">Confirm Password</Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Create Account
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardHeader>

          <CardContent>
            {/* Message Display */}
            {message && (
              <div
                className={`mt-4 p-3 rounded-lg text-sm ${message.isError
                  ? 'bg-destructive/10 text-destructive border border-destructive/20'
                  : 'bg-bullish/10 text-bullish border border-bullish/20'
                  }`}
              >
                {message.text}
              </div>
            )}

            {/* Continue without login */}
            <div className="mt-6 text-center">
              <p className="text-xs md:text-sm text-muted-foreground mb-2">
                Login required to access Stocxer AI dashboard
              </p>
              <Link
                href="/landing"
                className="text-xs md:text-sm text-primary hover:underline"
              >
                Learn more about Stocxer AI
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Features */}
        <div className="mt-6 md:mt-8 text-center space-y-2">
          <p className="text-xs md:text-sm text-muted-foreground">🤖 Powered by Watchman AI v3.5</p>
          <p className="text-xs md:text-sm text-muted-foreground">📊 Probability-Based Market Insights</p>
          <p className="text-xs md:text-sm text-muted-foreground">🎯 Deep Analysis & Decision Support</p>
        </div>
      </div>
    </div>
  )
}
