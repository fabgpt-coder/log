import { ref } from 'vue'
import { withBase } from 'vitepress'

const data = ref<any>(null)
const loaded = ref(false)
let promise: Promise<any> | null = null

export function usePRsData() {
  if (!promise && typeof window !== 'undefined') {
    promise = fetch(withBase('/prs.json'))
      .then((r) => r.json())
      .then((j) => {
        data.value = j
        loaded.value = true
        return j
      })
      .catch((e) => {
        console.error('failed to load prs.json', e)
        loaded.value = true
        return null
      })
  }
  return { data, loaded }
}

export function humanDuration(s: number | null | undefined): string {
  if (s == null) return '—'
  if (s < 60) return `${Math.round(s)}s`
  if (s < 3600) return `${Math.round(s / 60)}m`
  if (s < 86400) return `${(s / 3600).toFixed(1)}h`
  return `${(s / 86400).toFixed(1)}d`
}

export function ageFromTs(ts: number, nowTs: number = Math.floor(Date.now() / 1000)): string {
  return humanDuration(nowTs - ts)
}
