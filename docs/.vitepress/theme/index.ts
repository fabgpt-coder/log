import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import PRTable from './components/PRTable.vue'
import MetricsPanel from './components/MetricsPanel.vue'
import PulseStrip from './components/PulseStrip.vue'
import RepoHealth from './components/RepoHealth.vue'
import OldestOpen from './components/OldestOpen.vue'
import TitleBuckets from './components/TitleBuckets.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('PRTable', PRTable)
    app.component('MetricsPanel', MetricsPanel)
    app.component('PulseStrip', PulseStrip)
    app.component('RepoHealth', RepoHealth)
    app.component('OldestOpen', OldestOpen)
    app.component('TitleBuckets', TitleBuckets)
  },
} satisfies Theme
