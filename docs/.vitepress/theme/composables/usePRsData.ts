import { ref } from 'vue'
import { withBase } from 'vitepress'

const data = ref<any>(null)
const loaded = ref(false)
const error = ref<string | null>(null)
let promise: Promise<any> | null = null

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
  return { data, loaded, error }
}

// Re-export formatters for backward compatibility — new code should
// import directly from './formatters'.
export { humanDuration, ageFromTs } from './formatters'
