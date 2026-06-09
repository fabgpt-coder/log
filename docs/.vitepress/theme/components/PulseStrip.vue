<script setup lang="ts">
import { computed } from 'vue'
import { usePRsData, humanDuration } from '../composables/usePRsData'

const { data, loaded, error } = usePRsData()

const pulse = computed(() => data.value?.stats?.pulse || null)
</script>

<template>
  <div v-if="error" class="data-err">Failed to load stats: {{ error }}</div>
  <div class="pulse-strip" v-else-if="loaded && pulse">
    <div class="pulse-cell">
      <div class="lbl">Last PR opened</div>
      <div class="val">
        {{ humanDuration(pulse.last_pr_age_s) }}<span class="sfx" v-if="pulse.last_pr_age_s != null"> ago</span>
      </div>
    </div>
    <div class="pulse-cell">
      <div class="lbl">Last merge</div>
      <div class="val">
        {{ humanDuration(pulse.last_merge_age_s) }}<span class="sfx" v-if="pulse.last_merge_age_s != null"> ago</span>
      </div>
    </div>
    <div class="pulse-cell">
      <div class="lbl">Open right now</div>
      <div class="val">{{ pulse.open_count }}</div>
    </div>
    <div class="pulse-cell" :class="{ warn: pulse.stale_count > 0 }">
      <div class="lbl">Stale (&gt; {{ pulse.stale_threshold_days }}d)</div>
      <div class="val">{{ pulse.stale_count }}</div>
    </div>
  </div>
  <div v-else-if="loaded" class="loading">No pulse data.</div>
  <div v-else class="loading">Loading…</div>
</template>

<style scoped>
.pulse-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.5rem;
  margin: 1rem 0 1.5rem;
}

.pulse-cell {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 0.7rem 0.9rem;
}

.pulse-cell.warn {
  border-color: rgba(255, 180, 60, 0.6);
  background: rgba(255, 180, 60, 0.06);
}

.pulse-cell .lbl {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--vp-c-text-2);
  font-weight: 600;
}

.pulse-cell .val {
  font-size: 20px;
  font-weight: 700;
  margin-top: 0.2rem;
  font-variant-numeric: tabular-nums;
}

.pulse-cell .sfx {
  font-size: 12px;
  font-weight: 400;
  color: var(--vp-c-text-2);
}

.loading {
  color: var(--vp-c-text-2);
  font-size: 13px;
  padding: 0.5rem 0;
}

</style>
