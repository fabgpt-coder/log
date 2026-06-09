// Tiny query-string sync. Reads URL params on mount, writes them back on
// change via history.replaceState (no page reload, no router dep).
// Compatible with VitePress SSR: all calls are guarded by `window` checks.

import { watch, type Ref } from 'vue'

type Stringable = string | number | boolean | null | undefined

interface Field<T extends Stringable> {
  key: string
  ref: Ref<T>
  parse: (raw: string | null) => T
  serialize: (v: T) => string | null  // null → omit from URL
}

export function useQueryState(fields: Array<Field<any>>) {
  if (typeof window === 'undefined') return

  const url = new URL(window.location.href)

  // Hydrate from URL → refs.
  for (const f of fields) {
    const raw = url.searchParams.get(f.key)
    if (raw !== null) f.ref.value = f.parse(raw)
  }

  // Watch refs → URL. Debounced to coalesce typing bursts.
  let pending: number | null = null
  function flush() {
    pending = null
    const u = new URL(window.location.href)
    for (const f of fields) {
      const s = f.serialize(f.ref.value)
      if (s == null || s === '') u.searchParams.delete(f.key)
      else u.searchParams.set(f.key, s)
    }
    const next = u.pathname + (u.search ? u.search : '') + u.hash
    window.history.replaceState(null, '', next)
  }
  function schedule() {
    if (pending != null) clearTimeout(pending)
    pending = window.setTimeout(flush, 80) as unknown as number
  }
  for (const f of fields) watch(f.ref, schedule)
}

// Helper constructors for common types.

export function strField(key: string, ref: Ref<string>): Field<string> {
  return {
    key,
    ref,
    parse: (raw) => raw ?? '',
    serialize: (v) => (v ? v : null),
  }
}

export function intField(
  key: string,
  ref: Ref<number>,
  def: number = 0,
  opts: { min?: number; max?: number } = {},
): Field<number> {
  const { min = -Infinity, max = Infinity } = opts
  const clamp = (n: number) => Math.max(min, Math.min(max, n))
  return {
    key,
    ref,
    parse: (raw) => {
      const n = parseInt(raw ?? '', 10)
      return clamp(Number.isFinite(n) ? n : def)
    },
    serialize: (v) => (v === def ? null : String(clamp(v))),
  }
}

export function enumField<T extends string>(
  key: string,
  ref: Ref<T>,
  def: T,
  allowed: readonly T[],
): Field<T> {
  return {
    key,
    ref,
    parse: (raw) => (raw && (allowed as readonly string[]).includes(raw) ? (raw as T) : def),
    serialize: (v) => (v === def ? null : v),
  }
}
