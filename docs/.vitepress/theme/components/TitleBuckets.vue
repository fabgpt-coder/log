<script setup lang="ts">
import { computed } from 'vue'
import { usePRsData } from '../composables/usePRsData'

const { data, loaded, error } = usePRsData()

const buckets = computed<[string, number][]>(() =>
  (data.value?.stats?.title_buckets || []) as [string, number][]
)

const total = computed(() => buckets.value.reduce((acc, [, n]) => acc + n, 0))
const maxN = computed(() => buckets.value.reduce((m, [, n]) => Math.max(m, n), 0))

function pct(n: number): number {
  return total.value ? (n / total.value) * 100 : 0
}
</script>

<template>
  <div v-if="error" class="data-err">Failed to load stats: {{ error }}</div>
  <div class="bucket-wrap" v-else-if="loaded && buckets.length">
    <ul class="bucket-list">
      <li v-for="[name, n] in buckets" :key="name">
        <div class="bucket-row">
          <span class="bucket-label">{{ name }}</span>
          <span class="bucket-bar">
            <span class="fill" :style="{ width: maxN ? (n / maxN * 100) + '%' : '0%' }"></span>
          </span>
          <span class="bucket-count">{{ n }}</span>
          <span class="bucket-pct">{{ pct(n).toFixed(0) }}%</span>
        </div>
      </li>
    </ul>
    <div class="note">
      Classification by leading word / conventional-commit prefix / bot tag.
      {{ total }} PRs in total.
    </div>
  </div>
  <div v-else-if="loaded" class="loading">No titles yet.</div>
  <div v-else class="loading">Loading…</div>
</template>

<style scoped>
.bucket-wrap {
  margin: 1rem 0 2rem;
  font-size: 13px;
}

.bucket-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.bucket-row {
  display: grid;
  grid-template-columns: 12ch 1fr 5ch 5ch;
  align-items: center;
  gap: 0.7rem;
  padding: 0.3rem 0;
  border-bottom: 1px solid var(--vp-c-divider);
  font-variant-numeric: tabular-nums;
}

.bucket-label {
  font-weight: 600;
  color: var(--vp-c-text-1);
}

.bucket-bar {
  display: inline-block;
  height: 10px;
  background: var(--vp-c-bg-soft);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.bucket-bar .fill {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--vp-c-brand-1), var(--vp-c-brand-3));
  border-radius: 3px;
}

.bucket-count {
  text-align: right;
  color: var(--vp-c-text-2);
  font-size: 12px;
}

.bucket-pct {
  text-align: right;
  color: var(--vp-c-text-2);
  font-size: 12px;
}

.note {
  margin-top: 0.6rem;
  font-size: 11px;
  color: var(--vp-c-text-2);
}

.loading {
  color: var(--vp-c-text-2);
  font-size: 13px;
  padding: 0.5rem 0;
}
</style>
