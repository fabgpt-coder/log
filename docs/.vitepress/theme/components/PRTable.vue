<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { usePRsData } from '../composables/usePRsData'
import { useSortableTable } from '../composables/useSortableTable'
import { useQueryState, strField, enumField, intField } from '../composables/useQueryState'
import { fmtDate, truncate, debounce } from '../composables/formatters'
import { toCSV, downloadCSV } from '../composables/toCSV'

type PR = {
  date: string
  ts: number
  repo: string
  repo_short: string
  owner: string
  pr: number | null
  pr_url: string
  title: string
  state: string
  merged_at: string | null
  closed_at: string | null
  is_draft: boolean
  branch: string
  model: string
  endpoint: string
  plan_source: string
  guards: string[]
  verdict: string
  verdict_class: string
  entry_url: string
  source: string
}

const { data, loaded, error } = usePRsData()
const all = computed<PR[]>(() => (data.value?.prs || []) as PR[])

// Filters — bound to URL query string for shareable links.
const qInput = ref('')          // immediate input value (re-render-cheap)
const q = ref('')               // debounced version used by `filtered`
const repoFilter = ref('')
const stateFilter = ref('')
const pageSize = ref(50)
const page = ref(1)

// Debounce typing → big lists don't re-filter on every keystroke.
const setQDebounced = debounce((v: string) => { q.value = v }, 150)
watch(qInput, setQDebounced)

useQueryState([
  strField('q', qInput),
  strField('repo', repoFilter),
  strField('state', stateFilter),
  intField('size', pageSize, 50, { min: 25, max: 250 }),
  intField('page', page, 1, { min: 1, max: 10_000 }),
])

const repoOptions = computed(() =>
  Array.from(new Set(all.value.map((p) => p.repo_short).filter(Boolean))).sort(),
)
const stateOptions = computed(() =>
  Array.from(new Set(all.value.map((p) => p.state).filter(Boolean))).sort(),
)

const filtered = computed(() => {
  const ql = q.value.trim().toLowerCase()
  return all.value.filter((p) => {
    if (repoFilter.value && p.repo_short !== repoFilter.value) return false
    if (stateFilter.value && p.state !== stateFilter.value) return false
    if (!ql) return true
    return (
      p.repo.toLowerCase().includes(ql) ||
      (p.title || '').toLowerCase().includes(ql) ||
      (p.pr !== null && String(p.pr).includes(ql))
    )
  })
})

const { sorted, setSort, arrow, ariaSort } = useSortableTable<PR>(filtered, 'ts', 'desc')

// Reset to page 1 on any filter / sort change; clamp page on shrink.
watch([q, repoFilter, stateFilter], () => { page.value = 1 })
watch(sorted, (s) => {
  const max = Math.max(1, Math.ceil(s.length / pageSize.value))
  if (page.value > max) page.value = max
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(sorted.value.length / pageSize.value)),
)

const pageRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return sorted.value.slice(start, start + pageSize.value)
})

function reset() {
  qInput.value = ''
  q.value = ''
  repoFilter.value = ''
  stateFilter.value = ''
  pageSize.value = 50
  page.value = 1
}

function exportCSV() {
  const headers = ['date', 'repo', 'pr', 'state', 'title', 'url']
  const rows = sorted.value.map((p) => [
    p.date,
    p.repo,
    p.pr,
    p.state,
    p.title,
    p.pr_url,
  ])
  const today = new Date().toISOString().slice(0, 10)
  downloadCSV(`fabgpt-coder-prs-${today}.csv`, toCSV(headers, rows))
}

function verdictSymbol(cls: string) {
  return (
    ({
      clean: '✓',
      partial: '◐',
      failed: '✕',
      milestone: '★',
      merged: '✓',
      closed: '✕',
      open: '○',
      unknown: '·',
      other: '·',
    } as Record<string, string>)[cls] || '·'
  )
}

function stateClass(state: string) {
  return (
    ({
      merged: 'v-merged',
      closed: 'v-closed',
      open: 'v-open',
      unknown: 'v-other',
    } as Record<string, string>)[state] || 'v-other'
  )
}
</script>

<template>
  <div v-if="error" class="data-err">Failed to load PRs: {{ error }}</div>
  <div class="pr-table-wrap" v-else>
    <div class="pr-table-controls">
      <input
        v-model="qInput"
        type="search"
        placeholder="Search title, repo, PR#…"
        aria-label="Search PRs"
      />
      <select v-model="repoFilter" aria-label="Filter by repo">
        <option value="">All repos</option>
        <option v-for="r in repoOptions" :key="r" :value="r">{{ r }}</option>
      </select>
      <select v-model="stateFilter" aria-label="Filter by state">
        <option value="">All states</option>
        <option v-for="s in stateOptions" :key="s" :value="s">{{ s }}</option>
      </select>
      <button class="reset" @click="reset" type="button">Reset</button>
      <button class="reset" @click="exportCSV" type="button" :disabled="!sorted.length"
              :title="`Download ${sorted.length} rows as CSV`">↓ CSV</button>
      <span class="count">{{ sorted.length }} / {{ all.length }}</span>
    </div>

    <table class="pr-table" v-if="loaded && sorted.length > 0">
      <thead>
        <tr>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('ts')"
              @click="setSort('ts')"
              @keydown.enter.prevent="setSort('ts')"
              @keydown.space.prevent="setSort('ts')">
            When <span class="arrow">{{ arrow('ts') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('repo_short')"
              @click="setSort('repo_short')"
              @keydown.enter.prevent="setSort('repo_short')"
              @keydown.space.prevent="setSort('repo_short')">
            Repo · PR <span class="arrow">{{ arrow('repo_short') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('title')"
              @click="setSort('title')"
              @keydown.enter.prevent="setSort('title')"
              @keydown.space.prevent="setSort('title')">
            Title <span class="arrow">{{ arrow('title') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('state')"
              @click="setSort('state')"
              @keydown.enter.prevent="setSort('state')"
              @keydown.space.prevent="setSort('state')">
            State <span class="arrow">{{ arrow('state') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in pageRows" :key="p.repo + '#' + (p.pr ?? '∅') + '#' + p.ts">
          <td class="when" data-label="When">{{ fmtDate(p.date) }}</td>
          <td data-label="Repo · PR">
            <span class="repo">{{ p.owner }}/</span><code>{{ p.repo_short }}</code>
            &nbsp;
            <a v-if="p.pr_url" :href="p.pr_url" target="_blank" rel="noopener" class="pr-num">
              #{{ p.pr ?? '—' }}
            </a>
            <template v-else>#{{ p.pr ?? '—' }}</template>
          </td>
          <td class="title-cell" data-label="Title">
            <a v-if="p.pr_url" :href="p.pr_url" target="_blank" rel="noopener" :title="p.title">
              {{ truncate(p.title, 120) || '—' }}
            </a>
            <template v-else>{{ truncate(p.title, 120) || '—' }}</template>
          </td>
          <td data-label="State">
            <span class="verdict" :class="stateClass(p.state)">
              {{ verdictSymbol(p.state) }} {{ p.state }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else-if="loaded" class="empty">
      <p v-if="all.length === 0">
        No PRs logged yet. Once <code>fabgpt-coder</code> ships its first PR, it lands here.
      </p>
      <p v-else>No PRs match these filters.</p>
    </div>

    <div v-else class="empty">Loading…</div>

    <div class="pr-table-pager" v-if="totalPages > 1">
      <button :disabled="page <= 1" @click="page = 1" aria-label="First page">«</button>
      <button :disabled="page <= 1" @click="page--" aria-label="Previous page">‹ prev</button>
      <span>page {{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="page++" aria-label="Next page">next ›</button>
      <button :disabled="page >= totalPages" @click="page = totalPages" aria-label="Last page">»</button>
      <span class="page-size">
        per page
        <select v-model.number="pageSize" aria-label="Page size">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="250">250</option>
        </select>
      </span>
    </div>
  </div>
</template>
