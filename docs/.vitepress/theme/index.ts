import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import PRTable from './components/PRTable.vue'
import MetricsPanel from './components/MetricsPanel.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('PRTable', PRTable)
    app.component('MetricsPanel', MetricsPanel)
  },
} satisfies Theme
