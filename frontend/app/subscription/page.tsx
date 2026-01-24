import type { Metadata } from 'next'
import SubscriptionManager from '@/components/billing/SubscriptionManager'

export const metadata: Metadata = {
    title: 'Subscription Manager - Stocxer AI',
    description: 'Manage your subscription plan, view billing details, and upgrade or cancel your Stocxer AI subscription',
}

export default function SubscriptionPage() {
    return <SubscriptionManager />
}
