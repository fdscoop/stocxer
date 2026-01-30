'use client'

import * as React from 'react'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import PaperTradingDashboard from '@/components/trading/PaperTradingDashboard'

export default function PaperTradingPage() {
  const [user, setUser] = React.useState<{ email: string } | null>(null)

  React.useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      // User is logged in
      const email = localStorage.getItem('userEmail')
      setUser({ email: email || 'user@example.com' })
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    window.location.href = '/login'
  }

  return (
    <DashboardLayout user={user} onLogout={handleLogout}>
      <PaperTradingDashboard />
    </DashboardLayout>
  )
}

