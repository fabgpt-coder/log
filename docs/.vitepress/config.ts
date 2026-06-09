import { defineConfig } from 'vitepress'

// The site is published at https://fabgpt-coder.github.io/log/
// so we need the `/log/` base when building for production.
const isProd = process.env.NODE_ENV === 'production' || process.env.CI === 'true'

export default defineConfig({
  title: 'fabgpt-coder',
  description: 'Operations log of fabgpt-coder — every pull request shipped by the AI agent, with the receipts.',
  base: isProd ? '/log/' : '/',
  cleanUrls: true,
  lastUpdated: true,
  appearance: 'dark',
  head: [
    ['meta', { name: 'theme-color', content: '#0a0a0a' }],
    ['meta', { property: 'og:title', content: 'fabgpt-coder — operations log' }],
    ['meta', { property: 'og:description', content: 'Every PR shipped by my AI agent, with the receipts.' }],
    ['meta', { property: 'og:type', content: 'website' }],
  ],
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'All PRs', link: '/prs' },
      { text: 'GitHub', link: 'https://github.com/fabgpt-coder/log' },
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/fabgpt-coder/log' },
    ],
    search: { provider: 'local' },
    footer: {
      message: 'Auto-generated daily from <code>entries/*.md</code> frontmatter.',
      copyright: 'Built with VitePress · Source on <a href="https://github.com/fabgpt-coder/log">GitHub</a>',
    },
    outline: { level: [2, 3], label: 'On this page' },
  },
})
