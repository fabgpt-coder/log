<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { withBase } from 'vitepress'

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

type Payload = {
  generated_at: string
  stats: Record<string, any>
  prs: PR[]
}

const all = ref<PR[]>([])
const generatedAt = ref('')
const loaded = ref(false)

const q = ref('')
const repoFilter = ref('')
const modelFilter = ref('')
const stateFilter = ref('')
const verdictFilter = ref('')
const diaryOnly = ref(false)

const sortKey = ref<keyof PR | 'subs_pct'>('ts')
const sortDir = ref<'asc' | 'desc'>('desc')

const pageSize = ref(50)
const page = ref(1)

onMounted(async () => {
  try {
    const res = await fetch(withBase('/prs.json'))
    const j: Payload = await res.json()
    all.value = j.prs || []
    generatedAt.value = j.generated_at || ''
  } catch (e) {
    console.error('failed to load prs.json', e)
  } finally {
    loaded.value = true
  }
})

const repoOptions = computed(() =>
  Array.from(new Set(all.value.map(p => p.repo_short).filter(Boolean))).sort()
)
const modelOptions = computed(() =>
  Array.from(new Set(all.value.map(p => p.model).filter(Boolean))).sort()
)
const stateOptions = computed(() =>
  Array.from(new Set(all.value.map(p => p.state).filter(Boolean))).sort()
)
const verdictOptions = computed(() =>
  Array.from(new Set(all.value.map(p => p.verdict_class).filter(Boolean))).sort()
)

const filtered = computed(() => {
  const ql = q.value.trim().toLowerCase()
  return all.value.filter(p => {
    if (repoFilter.value && p.repo_short !== repoFilter.value) return false
    if (modelFilter.value && p.model !== modelFilter.value) return false
    if (stateFilter.value && p.state !== stateFilter.value) return false
    if (verdictFilter.value && p.verdict_class !== verdictFilter.value) return false
    if (diaryOnly.value && !p.entry_path) return false
    if (!ql) return true
    return (
      p.repo.toLowerCase().includes(ql) ||
      (p.title || '').toLowerCase().includes(ql) ||
      p.model.toLowerCase().includes(ql) ||
      p.model_full.toLowerCase().includes(ql) ||
      p.verdict.toLowerCase().includes(ql) ||
      p.branch.toLowerCase().includes(ql) ||
      p.endpoint.toLowerCase().includes(ql) ||
      p.plan_source.toLowerCase().includes(ql) ||
      p.guards.some(g => g.toLowerCase().includes(ql)) ||
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

function reset() {
  q.value = ''
  repoFilter.value = ''
  modelFilter.value = ''
  stateFilter.value = ''
  verdictFilter.value = ''
  diaryOnly.value = false
  sortKey.value = 'ts'
  sortDir.value = 'desc'
  page.value = 1
}

function fmtDate(iso: string) {
  if (!iso) return '—'
  return iso.slice(0, 16).replace('T', ' ')
}

function fmtSubs(p: PR) {
  if (!p.subs_den) return '—'
  return `${p.subs_num}/${p.subs_den}`
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
  <div class="pr-table-wrap">
    <div class="pr-table-controls">
      <input
        v-model="q"
        type="search"
        placeholder="Search title, repo, model, branch, guard, PR#…"
      />
      <select v-model="repoFilter" @change="page = 1">
        <option value="">All repos</option>
        <option v-for="r in repoOptions" :key="r" :value="r">{{ r }}</option>
      </select>
      <select v-model="stateFilter" @change="page = 1">
        <option value="">All states</option>
        <option v-for="s in stateOptions" :key="s" :value="s">{{ s }}</option>
      </select>
      <select v-model="modelFilter" @change="page = 1">
        <option value="">All models</option>
        <option v-for="m in modelOptions" :key="m" :value="m">{{ m }}</option>
      </select>
      <select v-model="verdictFilter" @change="page = 1">
        <option value="">All verdicts</option>
        <option v-for="v in verdictOptions" :key="v" :value="v">{{ v }}</option>
      </select>
      <label class="diary-toggle">
        <input type="checkbox" v-model="diaryOnly" @change="page = 1" />
        Diary only
      </label>
      <button class="reset" @click="reset">Reset</button>
      <span class="count">{{ sorted.length }} / {{ all.length }}</span>
    </div>

    <table class="pr-table" v-if="loaded && sorted.length > 0">
      <thead>
        <tr>
          <th @click="setSort('ts')">When <span class="arrow">{{ arrow('ts') }}</span></th>
          <th @click="setSort('repo_short')">Repo · PR <span class="arrow">{{ arrow('repo_short') }}</span></th>
          <th @click="setSort('title')">Title <span class="arrow">{{ arrow('title') }}</span></th>
          <th @click="setSort('state')">State <span class="arrow">{{ arrow('state') }}</span></th>
          <th @click="setSort('model')">Model <span class="arrow">{{ arrow('model') }}</span></th>
          <th @click="setSort('subs_pct')">Subs <span class="arrow">{{ arrow('subs_pct') }}</span></th>
          <th @click="setSort('verdict_class')">Verdict <span class="arrow">{{ arrow('verdict_class') }}</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in pageRows" :key="p.repo + '#' + p.pr">
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
          <td><code v-if="p.model">{{ p.model }}</code><template v-else>—</template></td>
          <td>{{ fmtSubs(p) }}<template v-if="p.subs_pct !== null"> ({{ p.subs_pct }}%)</template></td>
          <td>
            <template v-if="p.verdict_class && !['merged','closed','open','unknown'].includes(p.verdict_class)">
              <span class="verdict" :class="'v-' + p.verdict_class">
                {{ verdictSymbol(p.verdict_class) }} {{ p.verdict_class }}
              </span>
              <span class="verdict-text" v-if="p.verdict">{{ truncate(p.verdict, 60) }}</span>
            </template>
            <template v-else>—</template>
            <a v-if="p.entry_url" :href="p.entry_url" target="_blank" rel="noopener" class="entry-link">entry ↗</a>
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
