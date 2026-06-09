<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePRsData } from '../composables/usePRsData'
import { humanDuration, fmtDateShort } from '../composables/formatters'

type DailyPoint = {
  date: string
  opened: number
  resolved: number
  median_s: number | null
}

const { data, loaded, error } = usePRsData()
const mttr = computed(() => data.value?.stats?.mttr || { count: 0, mean_s: null, median_s: null, p90_s: null })
const series = computed<DailyPoint[]>(() => data.value?.stats?.daily_series?.series || [])

const hover = ref<number | null>(null)


// --- chart layout --------------------------------------------------------
const W = 720
const H = 200
const PAD_L = 36
const PAD_R = 36
const PAD_T = 16
const PAD_B = 22
const innerW = computed(() => W - PAD_L - PAD_R)
const innerH = computed(() => H - PAD_T - PAD_B)

const maxOpened = computed(() =>
  Math.max(1, ...series.value.map(p => p.opened))
)
const maxMedianS = computed(() => {
  const vals = series.value
    .map(p => p.median_s)
    .filter((v): v is number => v != null)
  return Math.max(1, ...vals)
})

function xFor(i: number): number {
  const n = series.value.length
  if (n <= 1) return PAD_L
  return PAD_L + (innerW.value * i) / (n - 1)
}

function barWidth(): number {
  const n = series.value.length || 1
  // Bars fit between adjacent x positions, with a little gap.
  return Math.max(2, (innerW.value / n) * 0.75)
}

function yForOpened(v: number): number {
  return PAD_T + innerH.value - (innerH.value * v) / maxOpened.value
}

function yForMedian(v: number): number {
  return PAD_T + innerH.value - (innerH.value * v) / maxMedianS.value
}

const linePath = computed(() => {
  let d = ''
  let started = false
  series.value.forEach((p, i) => {
    if (p.median_s == null) {
      started = false
      return
    }
    const x = xFor(i)
    const y = yForMedian(p.median_s)
    if (!started) {
      d += `M${x.toFixed(1)} ${y.toFixed(1)}`
      started = true
    } else {
      d += ` L${x.toFixed(1)} ${y.toFixed(1)}`
    }
  })
  return d
})

const xTickIndices = computed(() => {
  const n = series.value.length
  if (n <= 6) return series.value.map((_, i) => i)
  const step = Math.ceil(n / 6)
  const out: number[] = []
  for (let i = 0; i < n; i += step) out.push(i)
  if (out[out.length - 1] !== n - 1) out.push(n - 1)
  return out
})

const yTicksOpened = computed(() => {
  const m = maxOpened.value
  const step = m >= 50 ? 25 : m >= 20 ? 10 : m >= 10 ? 5 : m >= 4 ? 2 : 1
  const ticks: number[] = []
  for (let v = 0; v <= m; v += step) ticks.push(v)
  if (ticks[ticks.length - 1] !== m) ticks.push(m)
  return ticks
})

const hovered = computed(() => hover.value != null ? series.value[hover.value] : null)
</script>

<template>
  <div v-if="error" class="data-err">Failed to load stats: {{ error }}</div>
  <div class="metrics-panel" v-else-if="loaded">
    <div class="mttr-cards">
      <div class="card">
        <div class="card-label">Median MTTR</div>
        <div class="card-value">{{ humanDuration(mttr.median_s) }}</div>
        <div class="card-sub">across {{ mttr.count }} resolved PR{{ mttr.count === 1 ? '' : 's' }}</div>
      </div>
      <div class="card">
        <div class="card-label">Mean MTTR</div>
        <div class="card-value">{{ humanDuration(mttr.mean_s) }}</div>
        <div class="card-sub">long tail included</div>
      </div>
      <div class="card">
        <div class="card-label">p90 MTTR</div>
        <div class="card-value">{{ humanDuration(mttr.p90_s) }}</div>
        <div class="card-sub">90% close faster than this</div>
      </div>
    </div>

    <div class="chart-wrap">
      <div class="chart-title">
        Last 30 days
        <span class="legend">
          <span class="lg-bar"></span> opened/day
          <span class="lg-line"></span> median resolve time
        </span>
      </div>
      <svg :viewBox="`0 0 ${W} ${H}`" class="chart" preserveAspectRatio="xMidYMid meet">
        <!-- Y grid + left axis labels (opened) -->
        <g class="grid">
          <line
            v-for="t in yTicksOpened" :key="'g' + t"
            :x1="PAD_L" :x2="W - PAD_R"
            :y1="yForOpened(t)" :y2="yForOpened(t)"
          />
        </g>
        <g class="y-axis-l">
          <text
            v-for="t in yTicksOpened" :key="'yl' + t"
            :x="PAD_L - 6" :y="yForOpened(t) + 3"
            text-anchor="end"
          >{{ t }}</text>
        </g>

        <!-- Bars: opened per day -->
        <g class="bars">
          <rect
            v-for="(p, i) in series" :key="'b' + p.date"
            :x="xFor(i) - barWidth() / 2"
            :y="yForOpened(p.opened)"
            :width="barWidth()"
            :height="(PAD_T + innerH) - yForOpened(p.opened)"
          />
        </g>

        <!-- Line: median MTTR per day -->
        <path :d="linePath" class="line" fill="none" />
        <g class="dots">
          <template v-for="(p, i) in series" :key="'d' + p.date">
            <circle
              v-if="p.median_s != null"
              :cx="xFor(i)" :cy="yForMedian(p.median_s)"
              r="2.5"
            />
          </template>
        </g>

        <!-- X ticks -->
        <g class="x-axis">
          <line :x1="PAD_L" :x2="W - PAD_R" :y1="PAD_T + innerH" :y2="PAD_T + innerH" />
          <text
            v-for="i in xTickIndices" :key="'xt' + i"
            :x="xFor(i)" :y="PAD_T + innerH + 14"
            text-anchor="middle"
          >{{ fmtDateShort(series[i].date) }}</text>
        </g>

        <!-- Hover capture (one rect per column) -->
        <g class="hover-zones">
          <rect
            v-for="(p, i) in series" :key="'h' + p.date"
            :x="xFor(i) - innerW / (series.length || 1) / 2"
            :y="PAD_T"
            :width="innerW / (series.length || 1)"
            :height="innerH"
            fill="transparent"
            @mouseenter="hover = i"
            @mouseleave="hover = null"
          />
        </g>

        <!-- Hover indicator -->
        <g v-if="hover != null" class="hover-mark">
          <line
            :x1="xFor(hover)" :x2="xFor(hover)"
            :y1="PAD_T" :y2="PAD_T + innerH"
          />
        </g>
      </svg>

      <div class="tooltip" v-if="hovered">
        <strong>{{ hovered.date }}</strong> ·
        opened {{ hovered.opened }} ·
        resolved {{ hovered.resolved }} ·
        median {{ humanDuration(hovered.median_s) }}
      </div>
      <div class="tooltip placeholder" v-else>
        Hover the chart for daily numbers.
      </div>
    </div>
  </div>
</template>

<style scoped>
.metrics-panel {
  margin: 1.5rem 0 2rem;
}

.mttr-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.card {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  padding: 0.9rem 1rem;
}

.card-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--vp-c-text-2);
  font-weight: 600;
}

.card-value {
  font-size: 26px;
  font-weight: 700;
  margin-top: 0.25rem;
  font-variant-numeric: tabular-nums;
}

.card-sub {
  font-size: 11px;
  color: var(--vp-c-text-2);
  margin-top: 0.2rem;
}

.chart-wrap {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  padding: 0.9rem 1rem 0.75rem;
}

.chart-title {
  font-size: 12px;
  color: var(--vp-c-text-2);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.legend {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 11px;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
  color: var(--vp-c-text-2);
  margin-left: auto;
}

.lg-bar {
  display: inline-block;
  width: 12px;
  height: 8px;
  background: rgba(106, 208, 106, 0.55);
  margin-right: 0.2rem;
}

.lg-line {
  display: inline-block;
  width: 14px;
  height: 2px;
  background: #a78bfa;
  margin-left: 0.5rem;
  margin-right: 0.2rem;
}

.chart {
  width: 100%;
  height: auto;
  display: block;
}

.chart .grid line {
  stroke: var(--vp-c-divider);
  stroke-width: 1;
  stroke-dasharray: 2 4;
}

.chart .x-axis line {
  stroke: var(--vp-c-divider);
}

.chart .x-axis text,
.chart .y-axis-l text {
  fill: var(--vp-c-text-2);
  font-size: 10px;
  font-variant-numeric: tabular-nums;
}

.chart .bars rect {
  fill: rgba(106, 208, 106, 0.55);
}

.chart .line {
  stroke: #a78bfa;
  stroke-width: 2;
}

.chart .dots circle {
  fill: #a78bfa;
}

.chart .hover-mark line {
  stroke: var(--vp-c-text-2);
  stroke-width: 1;
  stroke-dasharray: 2 3;
  opacity: 0.6;
}

.tooltip {
  font-size: 12px;
  color: var(--vp-c-text-1);
  margin-top: 0.5rem;
  font-variant-numeric: tabular-nums;
}

.tooltip.placeholder {
  color: var(--vp-c-text-2);
}
</style>
