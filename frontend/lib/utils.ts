import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(num: number, decimals = 2): string {
  if (num >= 10000000) {
    return (num / 10000000).toFixed(decimals) + ' Cr'
  } else if (num >= 100000) {
    return (num / 100000).toFixed(decimals) + ' L'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(decimals) + 'K'
  }
  return num.toFixed(decimals)
}

export function formatPercent(num: number, decimals = 2): string {
  return num.toFixed(decimals) + '%'
}

export function formatCurrency(num: number): string {
  return '₹' + num.toLocaleString('en-IN')
}

export function getSignalColor(action: string): string {
  return action === 'BUY' ? 'text-bullish' : action === 'SELL' ? 'text-bearish' : 'text-neutral'
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 80) return 'text-bullish'
  if (confidence >= 60) return 'text-neutral'
  return 'text-bearish'
}
