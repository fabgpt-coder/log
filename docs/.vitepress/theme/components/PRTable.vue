<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { usePRsData } from '../composables/usePRsData'

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
  model_full: string
  endpoint: string
  plan_source: string
  subtasks_done: string
  subs_num: number
  subs_den: number
  subs_pct: number | null
  guards: string[]
  verdict: string
  verdict_class: string
  entry_path: string
  entry_url: string
  source: string
}

const { data, loaded, error } = usePRsData()
const all = computed<PR[]>(() => (data.value?.prs || []) as PR[])

const q = ref('')
const repoFilter = ref('')
const stateFilter = ref('')

const sortKey = ref<keyof PR | 'subs_pct'>('ts')
const sortDir = ref<'asc' | 'desc'>('desc')

const pageSize = ref(50)
const page = ref(1)

// Reset to page 1 whenever any filter changes — otherwise a filter that
// shrinks results below the current page leaves the table empty.
watch([q, repoFilter, stateFilter], () => { page.value = 1 })

const repoOptions = computed(() =>
  Array.from(new Set(all.value.map(p => p.repo_short).filter(Boolean))).sort()
)
const stateOptions = computed(() =>
  Array.from(new Set(all.value.map(p => p.state).filter(Boolean))).sort()
)

const filtered = computed(() => {
  const ql = q.value.trim().toLowerCase()
  return all.value.filter(p => {
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

const sorted = computed(() => {
  const k = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...filtered.value].sort((a, b) => {
    const av = (a as any)[k]
    const bv = (b as any)[k]
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (av < bv) return -1 * dir
    if (av > bv) return 1 * dir
    return 0
  })
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(sorted.value.length / pageSize.value))
)

const pageRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return sorted.value.slice(start, start + pageSize.value)
})

function setSort(k: keyof PR | 'subs_pct') {
  if (sortKey.value === k) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = k
    sortDir.value = k === 'ts' ? 'desc' : 'asc'
  }
  page.value = 1
}

function arrow(k: keyof PR | 'subs_pct') {
  if (sortKey.value !== k) return ''
  return sortDir.value === 'asc' ? '↑' : '↓'
}

function ariaSort(k: keyof PR | 'subs_pct'): 'ascending' | 'descending' | 'none' {
  if (sortKey.value !== k) return 'none'
  return sortDir.value === 'asc' ? 'ascending' : 'descending'
}

function reset() {
  q.value = ''
  repoFilter.value = ''
  stateFilter.value = ''
  sortKey.value = 'ts'
  sortDir.value = 'desc'
  page.value = 1
}

function fmtDate(iso: string) {
  if (!iso) return '—'
  return iso.slice(0, 16).replace('T', ' ')
}

function verdictSymbol(cls: string) {
  return ({
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
}

function stateClass(state: string) {
  return ({
    merged: 'v-merged',
    closed: 'v-closed',
    open: 'v-open',
    unknown: 'v-other',
  } as Record<string, string>)[state] || 'v-other'
}

function truncate(s: string, n = 80) {
  if (!s) return ''
  return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s
}
</script>

<template>
  <div v-if="error" class="data-err">Failed to load PRs: {{ error }}</div>
  <div class="pr-table-wrap" v-else>
    <div class="pr-table-controls">
      <input
        v-model="q"
        type="search"
        placeholder="Search title, repo, PR#…"
      />
      <select v-model="repoFilter">
        <option value="">All repos</option>
        <option v-for="r in repoOptions" :key="r" :value="r">{{ r }}</option>
      </select>
      <select v-model="stateFilter">
        <option value="">All states</option>
        <option v-for="s in stateOptions" :key="s" :value="s">{{ s }}</option>
      </select>
      <button class="reset" @click="reset">Reset</button>
      <span class="count">{{ sorted.length }} / {{ all.length }}</span>
    </div>

    <table class="pr-table" v-if="loaded && sorted.length > 0">
      <thead>
        <tr>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('ts')"
              @click="setSort('ts')" @keydown.enter.prevent="setSort('ts')" @keydown.space.prevent="setSort('ts')">
            When <span class="arrow">{{ arrow('ts') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('repo_short')"
              @click="setSort('repo_short')" @keydown.enter.prevent="setSort('repo_short')" @keydown.space.prevent="setSort('repo_short')">
            Repo · PR <span class="arrow">{{ arrow('repo_short') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('title')"
              @click="setSort('title')" @keydown.enter.prevent="setSort('title')" @keydown.space.prevent="setSort('title')">
            Title <span class="arrow">{{ arrow('title') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('state')"
              @click="setSort('state')" @keydown.enter.prevent="setSort('state')" @keydown.space.prevent="setSort('state')">
            State <span class="arrow">{{ arrow('state') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in pageRows" :key="p.repo + '#' + (p.pr ?? '∅') + '#' + p.ts">
          <td class="when">{{ fmtDate(p.date) }}</td>
          <td>
            <span class="repo">{{ p.owner }}/</span><code>{{ p.repo_short }}</code>
            &nbsp;
            <a v-if="p.pr_url" :href="p.pr_url" target="_blank" rel="noopener" class="pr-num">
              #{{ p.pr ?? '—' }}
            </a>
            <template v-else>#{{ p.pr ?? '—' }}</template>
          </td>
          <td class="title-cell">
            <a v-if="p.pr_url" :href="p.pr_url" target="_blank" rel="noopener" :title="p.title">
              {{ truncate(p.title, 80) || '—' }}
            </a>
            <template v-else>{{ truncate(p.title, 80) || '—' }}</template>
          </td>
          <td>
            <span class="verdict" :class="stateClass(p.state)">
              {{ verdictSymbol(p.state) }} {{ p.state }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else-if="loaded" class="empty">
      <p v-if="all.length === 0">No PRs logged yet. Once <code>fabgpt-coder</code> ships its first PR, it lands here.</p>
      <p v-else>No PRs match these filters.</p>
    </div>

    <div v-else class="empty">Loading…</div>

    <div class="pr-table-pager" v-if="totalPages > 1">
      <button :disabled="page <= 1" @click="page = 1">«</button>
      <button :disabled="page <= 1" @click="page--">‹ prev</button>
      <span>page {{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="page++">next ›</button>
      <button :disabled="page >= totalPages" @click="page = totalPages">»</button>
      <span style="margin-left:auto">
        per page
        <select v-model.number="pageSize" @change="page = 1">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="250">250</option>
        </select>
      </span>
    </div>
  </div>
</template>
