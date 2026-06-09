// Client-side CSV download. RFC 4180-ish: quotes are doubled inside fields,
// every field is wrapped in quotes, line ending is \r\n.

export function toCSV(headers: string[], rows: (string | number | null | undefined)[][]): string {
  const escape = (v: string | number | null | undefined) => {
    const s = v == null ? '' : String(v)
    return '"' + s.replace(/"/g, '""') + '"'
  }
  const lines = [headers.map(escape).join(',')]
  for (const r of rows) lines.push(r.map(escape).join(','))
  return lines.join('\r\n')
}

export function downloadCSV(filename: string, csv: string): void {
  if (typeof window === 'undefined') return
  // BOM so Excel auto-detects UTF-8 (titles contain emoji).
  const blob = new Blob(['﻿', csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 0)
}
