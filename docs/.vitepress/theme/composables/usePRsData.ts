import { ref } from 'vue'
import { withBase } from 'vitepress'

const data = ref<any>(null)
const loaded = ref(false)
const error = ref<string | null>(null)
let promise: Promise<any> | null = null

// Reactive "now" that ticks every 60s on the client. Anywhere ageFromTs()
// is called in a template, the template re-renders on each tick — so "3h
// ago" labels stay fresh on long-open tabs without a page reload.
const nowTs = ref(typeof window !== 'undefined' ? Math.floor(Date.now() / 1000) : 0)
if (typeof window !== 'undefined') {
  setInterval(() => {
    nowTs.value = Math.floor(Date.now() / 1000)
  }, 60_000)
}

export function usePRsData() {
  if (!promise && typeof window !== 'undefined') {
    promise = fetch(withBase('/prs.json'))
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status} ${r.statusText}`)
        return r.json()
      })
      .then((j) => {
        data.value = j
        error.value = null
        loaded.value = true
        return j
      })
      .catch((e) => {
        // Reset the singleton so a re-mount triggers a fresh fetch.
        promise = null
        error.value = String(e?.message || e)
        loaded.value = true
        console.error('failed to load prs.json', e)
        return null
      })
  }
  return { data, loaded, error, nowTs }
}

export function humanDuration(s: number | null | undefined): string {
  if (s == null) return '—'
  if (s < 60) return `${Math.round(s)}s`
  if (s < 3600) return `${Math.round(s / 60)}m`
  if (s < 86400) return `${(s / 3600).toFixed(1)}h`
  return `${(s / 86400).toFixed(1)}d`
}

// Reads the reactive `nowTs` so any template calling this auto-refreshes
// when the ticker fires (Vue tracks the read during render).
export function ageFromTs(ts: number): string {
  return humanDuration(nowTs.value - ts)
}
