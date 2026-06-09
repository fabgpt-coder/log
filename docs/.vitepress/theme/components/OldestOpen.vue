<script setup lang="ts">
import { computed } from 'vue'
import { usePRsData, ageFromTs } from '../composables/usePRsData'

type Row = {
  repo: string
  repo_short: string
  owner: string
  pr: number
  pr_url: string
  title: string
  date: string
  ts: number
}

const { data, loaded } = usePRsData()
const rows = computed<Row[]>(() => data.value?.stats?.oldest_open || [])

function truncate(s: string, n = 80): string {
  if (!s) return ''
  return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s
}
</script>

<template>
  <div class="oldest-wrap" v-if="loaded && rows.length">
    <table class="oldest">
      <thead>
        <tr>
          <th>Age</th>
          <th>Repo · PR</th>
          <th>Title</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.repo + '#' + r.pr">
          <td class="age">{{ ageFromTs(r.ts) }}</td>
          <td>
            <a :href="r.pr_url" target="_blank" rel="noopener">
              <span class="owner">{{ r.owner }}/</span><code>{{ r.repo_short }}</code>
              <span class="pr-num"> #{{ r.pr }}</span>
            </a>
          </td>
          <td class="title-cell">
            <a :href="r.pr_url" target="_blank" rel="noopener" :title="r.title">
              {{ truncate(r.title, 90) }}
            </a>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="note">Showing the {{ rows.length }} oldest still-open PRs. Older = riper for review or close.</div>
  </div>
  <div v-else-if="loaded" class="loading">No open PRs.</div>
  <div v-else class="loading">Loading…</div>
</template>

<style scoped>
.oldest-wrap {
  margin: 1rem 0 2rem;
  font-size: 13px;
}

.oldest {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

.oldest th,
.oldest td {
  border-bottom: 1px solid var(--vp-c-divider);
  padding: 0.5rem 0.6rem;
  text-align: left;
  vertical-align: middle;
}

.oldest th {
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--vp-c-text-2);
  font-weight: 600;
}

.oldest tr:hover td {
  background: var(--vp-c-bg-soft);
}

.oldest code {
  font-size: 12px;
  background: var(--vp-c-bg-soft);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
}

.oldest .owner {
  color: var(--vp-c-text-3);
  font-size: 12px;
}

.oldest .pr-num {
  font-weight: 600;
  color: var(--vp-c-text-1);
}

.oldest a {
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.oldest a:hover {
  color: var(--vp-c-brand-1);
}

.age {
  white-space: nowrap;
  color: #d9a949;
  font-weight: 600;
}

.title-cell {
  max-width: 50ch;
  overflow: hidden;
  text-overflow: ellipsis;
}

.note {
  margin-top: 0.5rem;
  font-size: 11px;
  color: var(--vp-c-text-2);
}

.loading {
  color: var(--vp-c-text-2);
  font-size: 13px;
  padding: 0.5rem 0;
}
</style>
