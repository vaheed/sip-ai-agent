export const formatTimestamp = (seconds: number | null | undefined) => {
  if (!seconds) {
    return '—'
  }
  const date = new Date(seconds * 1000)
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date)
}

export const formatDuration = (start: number, end?: number | null, nowSeconds?: number) => {
  const effectiveEnd = typeof end === 'number' ? end : nowSeconds ?? Date.now() / 1000
  const totalSeconds = Math.max(0, Math.round(effectiveEnd - start))
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${seconds}s`
}
