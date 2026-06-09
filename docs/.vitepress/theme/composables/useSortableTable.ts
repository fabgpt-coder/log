import { ref, computed, type Ref } from 'vue'

type Dir = 'asc' | 'desc'

export interface SortableTable<T, K extends keyof T = keyof T> {
  sortKey: Ref<K>
  sortDir: Ref<Dir>
  sorted: Ref<T[]>
  setSort: (k: K) => void
  arrow: (k: K) => string
  ariaSort: (k: K) => 'ascending' | 'descending' | 'none'
}

export function useSortableTable<T extends object, K extends keyof T = keyof T>(
  rows: Ref<T[]>,
  initialKey: K,
  initialDir: Dir = 'desc',
): SortableTable<T, K> {
  const sortKey = ref(initialKey) as Ref<K>
  const sortDir = ref<Dir>(initialDir)

  const sorted = computed(() => {
    const k = sortKey.value
    const dir = sortDir.value === 'asc' ? 1 : -1
    return [...rows.value].sort((a, b) => {
      const av = a[k] as any
      const bv = b[k] as any
      // Nulls always sort to the end regardless of direction.
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      if (av < bv) return -1 * dir
      if (av > bv) return 1 * dir
      return 0
    })
  })

  function setSort(k: K) {
    if (sortKey.value === k) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortKey.value = k
      sortDir.value = 'desc'
    }
  }

  function arrow(k: K) {
    if (sortKey.value !== k) return ''
    return sortDir.value === 'asc' ? '↑' : '↓'
  }

  function ariaSort(k: K): 'ascending' | 'descending' | 'none' {
    if (sortKey.value !== k) return 'none'
    return sortDir.value === 'asc' ? 'ascending' : 'descending'
  }

  return { sortKey, sortDir, sorted, setSort, arrow, ariaSort }
}
