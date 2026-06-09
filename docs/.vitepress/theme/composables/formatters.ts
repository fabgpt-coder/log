// Formatting helpers shared across components.

import { ref } from 'vue'

// Reactive "now" — ticks every 60s on the client. Anywhere ageFromTs() is
// used in a template, the template re-renders on each tick.
const nowTs = ref(typeof window !== 'undefined' ? Math.floor(Date.now() / 1000) : 0)
if (typeof window !== 'undefined') {
  setInterval(() => {
    nowTs.value = Math.floor(Date.now() / 1000)
  }, 60_000)
}

export function humanDuration(s: number | null | undefined): string {
  if (s == null) return '—'
  if (s < 0) s = 0
  if (s < 60) return `${Math.round(s)}s`
  if (s < 3600) return `${Math.round(s / 60)}m`
  if (s < 86400) return `${(s / 3600).toFixed(1)}h`
  return `${(s / 86400).toFixed(1)}d`
}

export function ageFromTs(ts: number | null | undefined): string {
  if (ts == null || ts === 0) return '—'
  return humanDuration(nowTs.value - ts)
}

export function truncate(s: string | null | undefined, n: number = 80): string {
  if (!s) return ''
  return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return iso.slice(0, 16).replace('T', ' ')
}

export function fmtDateShort(iso: string | null | undefined): string {
  if (!iso) return '—'
  return iso.slice(5, 10) // MM-DD
}

export function fmtPct(v: number | null | undefined, digits: number = 0): string {
  if (v == null) return '—'
  return (v * 100).toFixed(digits) + '%'
}

// Debounce a function — useful for search inputs over large lists.
export function debounce<T extends (...a: any[]) => any>(fn: T, ms: number): (...a: Parameters<T>) => void {
  let t: number | null = null
  return (...args: Parameters<T>) => {
    if (t != null) clearTimeout(t)
    t = window.setTimeout(() => fn(...args), ms) as unknown as number
  }
}
