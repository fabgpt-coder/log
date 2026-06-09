<script setup lang="ts">
import { computed } from 'vue'
import { usePRsData } from '../composables/usePRsData'
import { useSortableTable } from '../composables/useSortableTable'
import { humanDuration, ageFromTs, fmtPct } from '../composables/formatters'

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
const rows = computed<Row[]>(() => (data.value?.stats?.repo_health || []) as Row[])

const { sorted, setSort, arrow, ariaSort } = useSortableTable<Row>(rows, 'total', 'desc')

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
              @click="setSort('repo_short')"
              @keydown.enter.prevent="setSort('repo_short')"
              @keydown.space.prevent="setSort('repo_short')">
            Repo <span class="arrow">{{ arrow('repo_short') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('total')" class="num"
              @click="setSort('total')"
              @keydown.enter.prevent="setSort('total')"
              @keydown.space.prevent="setSort('total')">
            PRs <span class="arrow">{{ arrow('total') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('merged')" class="num"
              @click="setSort('merged')"
              @keydown.enter.prevent="setSort('merged')"
              @keydown.space.prevent="setSort('merged')">
            Merged <span class="arrow">{{ arrow('merged') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('closed')" class="num"
              @click="setSort('closed')"
              @keydown.enter.prevent="setSort('closed')"
              @keydown.space.prevent="setSort('closed')">
            Closed <span class="arrow">{{ arrow('closed') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('open')" class="num"
              @click="setSort('open')"
              @keydown.enter.prevent="setSort('open')"
              @keydown.space.prevent="setSort('open')">
            Open <span class="arrow">{{ arrow('open') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('merge_rate')"
              @click="setSort('merge_rate')"
              @keydown.enter.prevent="setSort('merge_rate')"
              @keydown.space.prevent="setSort('merge_rate')"
              title="merged / (merged + closed) — acceptance rate among resolved PRs">
            Accept % <span class="arrow">{{ arrow('merge_rate') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('median_mttr_s')"
              @click="setSort('median_mttr_s')"
              @keydown.enter.prevent="setSort('median_mttr_s')"
              @keydown.space.prevent="setSort('median_mttr_s')">
            Median MTTR <span class="arrow">{{ arrow('median_mttr_s') }}</span>
          </th>
          <th scope="col" tabindex="0" role="button" :aria-sort="ariaSort('last_activity_ts')"
              @click="setSort('last_activity_ts')"
              @keydown.enter.prevent="setSort('last_activity_ts')"
              @keydown.space.prevent="setSort('last_activity_ts')">
            Last activity <span class="arrow">{{ arrow('last_activity_ts') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in sorted" :key="r.repo">
          <td data-label="Repo">
            <a :href="repoHref(r.repo)" target="_blank" rel="noopener">
              <span class="owner">{{ r.owner }}/</span><code>{{ r.repo_short }}</code>
            </a>
          </td>
          <td class="num" data-label="PRs">{{ r.total }}</td>
          <td class="num" data-label="Merged">{{ r.merged }}</td>
          <td class="num" data-label="Closed">{{ r.closed }}</td>
          <td class="num" data-label="Open">{{ r.open }}</td>
          <td data-label="Accept %">
            <div class="rate">
              <div class="bar" :class="mergeBarClass(r.merge_rate)">
                <div class="fill" :style="{ width: r.merge_rate != null ? (r.merge_rate * 100).toFixed(1) + '%' : '0%' }"></div>
              </div>
              <span class="rate-text">{{ fmtPct(r.merge_rate) }}</span>
            </div>
          </td>
          <td data-label="Median MTTR">{{ humanDuration(r.median_mttr_s) }}</td>
          <td class="when" data-label="Last activity">{{ ageFromTs(r.last_activity_ts) }} ago</td>
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
  color: var(--vp-c-text-2);
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

.bar-good .fill { background: #6ad06a; }
.bar-ok .fill   { background: #d9a949; }
.bar-warn .fill { background: #e86464; }
.bar-neutral .fill { background: var(--vp-c-text-3); }

.rate-text {
  font-size: 12px;
  color: var(--vp-c-text-2);
  min-width: 3ch;
}

.when {
  color: var(--vp-c-text-2);
  font-size: 12px;
  white-space: nowrap;
}

.loading {
  color: var(--vp-c-text-2);
  font-size: 13px;
  padding: 0.5rem 0;
}

/* Mobile: stack as cards. Each row becomes a labeled block. */
@media (max-width: 720px) {
  .repo-health,
  .repo-health thead,
  .repo-health tbody,
  .repo-health tr,
  .repo-health td {
    display: block;
    width: 100%;
  }
  .repo-health thead {
    position: absolute;
    left: -9999px;  /* visually hidden but still in tree for AT */
  }
  .repo-health tr {
    border: 1px solid var(--vp-c-divider);
    border-radius: 8px;
    margin-bottom: 0.5rem;
    padding: 0.25rem 0.5rem;
  }
  .repo-health td {
    border: none;
    padding: 0.25rem 0;
    display: grid;
    grid-template-columns: 11ch 1fr;
    gap: 0.5rem;
    text-align: left !important;
    align-items: center;
  }
  .repo-health td::before {
    content: attr(data-label);
    color: var(--vp-c-text-2);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
  }
  .repo-health td.num { text-align: left !important; }
  .repo-health tr:hover td { background: transparent; }
}
</style>
