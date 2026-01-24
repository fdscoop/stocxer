import type { Metadata } from 'next'
import BillingDashboard from '@/components/billing/BillingDashboard'

export const metadata: Metadata = {
    title: 'Billing & Credits - Stocxer AI',
    description: 'Manage your subscription, credits, and billing for Stocxer AI trading platform',
}

export default function BillingPage() {
    return <BillingDashboard />
}
