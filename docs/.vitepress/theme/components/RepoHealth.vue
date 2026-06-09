<script setup lang="ts">
import { computed, ref } from 'vue'
import { usePRsData, humanDuration, ageFromTs } from '../composables/usePRsData'

type Row = {
  repo: string
  repo_short: string
  owner: string
  total: number
  merged: number
  closed: number
  open: number
  merge_rate: number | null
  median_mttr_s: number | null
  last_activity_ts: number
}

const { data, loaded, error } = usePRsData()
const rows = computed<Row[]>(() => data.value?.stats?.repo_health || [])

type Key = keyof Row
const sortKey = ref<Key>('total')
const sortDir = ref<'asc' | 'desc'>('desc')

function setSort(k: Key) {
  if (sortKey.value === k) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else {
    sortKey.value = k
    sortDir.value = k === 'repo_short' ? 'asc' : 'desc'
  }
}

const sorted = computed(() => {
  const k = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...rows.value].sort((a, b) => {
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

function arrow(k: Key) {
  if (sortKey.value !== k) return ''
  return sortDir.value === 'asc' ? '↑' : '↓'
}

function ariaSort(k: Key): 'ascending' | 'descending' | 'none' {
  if (sortKey.value !== k) return 'none'
  return sortDir.value === 'asc' ? 'ascending' : 'descending'
}

function fmtPct(v: number | null): string {
  if (v == null) return '—'
  return Math.round(v * 100) + '%'
}

function repoHref(repo: string) {
  return `https://github.com/${repo}`
}

function mergeBarClass(v: number | null): string {
  if (v == null) return 'bar-neutral'
  if (v >= 0.8) return 'bar-good'
  if (v >= 0.5) return 'bar-ok'
  return 'bar-warn'
}
</script>

<template>
  <div v-if="error" class="data-err">Failed to load stats: {{ error }}</div>
  <div class="repo-health-wrap" v-else-if="loaded && sorted.length">
    <table class="repo-health">
      <thead>
        <tr>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('repo_short')"
              @click="setSort('repo_short')" @keydown.enter.prevent="setSort('repo_short')" @keydown.space.prevent="setSort('repo_short')">
            Repo <span class="arrow">{{ arrow('repo_short') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('total')" class="num"
              @click="setSort('total')" @keydown.enter.prevent="setSort('total')" @keydown.space.prevent="setSort('total')">
            PRs <span class="arrow">{{ arrow('total') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('merged')" class="num"
              @click="setSort('merged')" @keydown.enter.prevent="setSort('merged')" @keydown.space.prevent="setSort('merged')">
            Merged <span class="arrow">{{ arrow('merged') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('closed')" class="num"
              @click="setSort('closed')" @keydown.enter.prevent="setSort('closed')" @keydown.space.prevent="setSort('closed')">
            Closed <span class="arrow">{{ arrow('closed') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('open')" class="num"
              @click="setSort('open')" @keydown.enter.prevent="setSort('open')" @keydown.space.prevent="setSort('open')">
            Open <span class="arrow">{{ arrow('open') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('merge_rate')"
              @click="setSort('merge_rate')" @keydown.enter.prevent="setSort('merge_rate')" @keydown.space.prevent="setSort('merge_rate')"
              title="merged / (merged + closed) — acceptance rate among resolved PRs">
            Accept % <span class="arrow">{{ arrow('merge_rate') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('median_mttr_s')"
              @click="setSort('median_mttr_s')" @keydown.enter.prevent="setSort('median_mttr_s')" @keydown.space.prevent="setSort('median_mttr_s')">
            Median MTTR <span class="arrow">{{ arrow('median_mttr_s') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('last_activity_ts')"
              @click="setSort('last_activity_ts')" @keydown.enter.prevent="setSort('last_activity_ts')" @keydown.space.prevent="setSort('last_activity_ts')">
            Last activity <span class="arrow">{{ arrow('last_activity_ts') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in sorted" :key="r.repo">
          <td>
            <a :href="repoHref(r.repo)" target="_blank" rel="noopener">
              <span class="owner">{{ r.owner }}/</span><code>{{ r.repo_short }}</code>
            </a>
          </td>
          <td class="num">{{ r.total }}</td>
          <td class="num">{{ r.merged }}</td>
          <td class="num">{{ r.closed }}</td>
          <td class="num">{{ r.open }}</td>
          <td>
            <div class="rate">
              <div class="bar" :class="mergeBarClass(r.merge_rate)">
                <div class="fill" :style="{ width: r.merge_rate != null ? (r.merge_rate * 100) + '%' : '0%' }"></div>
              </div>
              <span class="rate-text">{{ fmtPct(r.merge_rate) }}</span>
            </div>
          </td>
          <td>{{ humanDuration(r.median_mttr_s) }}</td>
          <td class="when">{{ ageFromTs(r.last_activity_ts) }} ago</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div v-else-if="loaded" class="loading">No repos yet.</div>
  <div v-else class="loading">Loading…</div>
</template>

<style scoped>
.repo-health-wrap {
  margin: 1rem 0 2rem;
  font-size: 13px;
  overflow-x: auto;
}

.repo-health th:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: -2px;
  border-radius: 4px;
}

.repo-health {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

.repo-health th,
.repo-health td {
  border-bottom: 1px solid var(--vp-c-divider);
  padding: 0.5rem 0.6rem;
  text-align: left;
  vertical-align: middle;
}

.repo-health th {
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--vp-c-text-2);
  cursor: pointer;
  user-select: none;
  font-weight: 600;
}

.repo-health th .arrow {
  display: inline-block;
  width: 1ch;
  margin-left: 0.2rem;
  color: var(--vp-c-brand-1);
}

.repo-health td.num,
.repo-health th.num {
  text-align: right;
}

.repo-health tr:hover td {
  background: var(--vp-c-bg-soft);
}

.repo-health code {
  font-size: 12px;
  background: var(--vp-c-bg-soft);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
}

.repo-health .owner {
  color: var(--vp-c-text-3);
  font-size: 12px;
}

.repo-health a {
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.repo-health a:hover {
  color: var(--vp-c-brand-1);
}

.rate {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bar {
  width: 90px;
  height: 7px;
  background: var(--vp-c-divider);
  border-radius: 3px;
  overflow: hidden;
}

.bar .fill {
  height: 100%;
  border-radius: 3px;
}

.bar-good .fill {
  background: #6ad06a;
}

.bar-ok .fill {
  background: #d9a949;
}

.bar-warn .fill {
  background: #e86464;
}

.bar-neutral .fill {
  background: var(--vp-c-text-3);
}

.rate-text {
  font-size: 12px;
  color: var(--vp-c-text-2);
  min-width: 3ch;
}

.when {
  color: var(--vp-c-text-2);
  font-size: 12px;
}

.loading {
  color: var(--vp-c-text-2);
  font-size: 13px;
  padding: 0.5rem 0;
}
</style>
