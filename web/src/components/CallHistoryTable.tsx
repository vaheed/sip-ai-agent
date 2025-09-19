import { useEffect, useState } from 'react'
import { ArrowDownTrayIcon, ClockIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

import type { CallHistoryItem } from '../types'
import { formatDuration, formatTimestamp } from '../utils/time'

interface CallHistoryTableProps {
  history: CallHistoryItem[]
}

export const CallHistoryTable = ({ history }: CallHistoryTableProps) => {
  const [isCompact, setIsCompact] = useState<boolean>(() => {
    if (typeof window === 'undefined') {
      return false
    }
    return window.innerWidth < 768
  })

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return
    }
    const mediaQuery = window.matchMedia('(max-width: 767px)')
    const handleChange = (event: MediaQueryListEvent | MediaQueryList) => {
      setIsCompact(event.matches)
    }

    handleChange(mediaQuery)

    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }

    mediaQuery.addListener(handleChange)
    return () => mediaQuery.removeListener(handleChange)
  }, [])

  return (
    <div className="overflow-hidden rounded-3xl border border-white/60 bg-white/80 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-white/5">
      <div className="flex flex-col gap-3 border-b border-slate-200/70 bg-gradient-to-r from-white/70 to-white/30 px-6 py-5 dark:border-white/10 dark:from-white/10 dark:to-white/5 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Call History</h2>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Completed and in-progress calls</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Review connection outcomes or export the latest records.</p>
        </div>
        <a
          href="/api/call_history.csv"
          download="call-history.csv"
          className="inline-flex items-center justify-center gap-2 self-start rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 dark:bg-blue-500 dark:hover:bg-blue-400 dark:focus:ring-offset-slate-900"
        >
          <ArrowDownTrayIcon className="h-4 w-4" />
          Download CSV
        </a>
      </div>

      {history.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-4 px-6 py-12 text-center text-sm text-slate-500 dark:text-slate-400">
          <DocumentTextIcon className="h-10 w-10" />
          <p>Call history will appear once calls are completed.</p>
        </div>
      ) : isCompact ? (
        <div className="divide-y divide-slate-200 text-sm text-slate-700 dark:divide-slate-800 dark:text-slate-200">
          {history.map((item) => {
            const isActive = item.end === null
            return (
              <div key={`${item.call_id}-${item.start}`} className="flex flex-col gap-3 px-5 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Call {item.call_id}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Correlation {item.correlation_id ?? '—'}</p>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${
                      isActive
                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-100'
                        : 'bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-200'
                    }`}
                  >
                    <ClockIcon className="h-4 w-4" />
                    {isActive ? 'In progress' : 'Completed'}
                  </span>
                </div>
                <div className="grid gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <div className="flex items-center justify-between">
                    <span className="uppercase tracking-wide">Started</span>
                    <span className="text-slate-700 dark:text-slate-200">{formatTimestamp(item.start)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="uppercase tracking-wide">Ended</span>
                    <span className="text-slate-700 dark:text-slate-200">{formatTimestamp(item.end ?? undefined)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="uppercase tracking-wide">Duration</span>
                    <span className="text-slate-700 dark:text-slate-200">{formatDuration(item.start, item.end)}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
            <thead className="bg-slate-50/70 text-left text-xs uppercase tracking-wide text-slate-500 dark:bg-white/5 dark:text-slate-400">
              <tr>
                  <th className="px-6 py-3">Call ID</th>
                  <th className="px-6 py-3">Correlation</th>
                  <th className="px-6 py-3">Started</th>
                  <th className="px-6 py-3">Ended</th>
                  <th className="px-6 py-3">Duration</th>
                  <th className="px-6 py-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700 dark:divide-slate-800 dark:text-slate-200">
                {history.map((item) => {
                  const isActive = item.end === null
                  return (
                    <tr key={`${item.call_id}-${item.start}`} className="hover:bg-slate-50/60 dark:hover:bg-white/5">
                      <td className="whitespace-nowrap px-6 py-4 font-semibold">{item.call_id}</td>
                      <td className="px-6 py-4 text-xs text-slate-500 dark:text-slate-400">{item.correlation_id ?? '—'}</td>
                      <td className="px-6 py-4">{formatTimestamp(item.start)}</td>
                      <td className="px-6 py-4">{formatTimestamp(item.end ?? undefined)}</td>
                      <td className="px-6 py-4 text-sm">{formatDuration(item.start, item.end)}</td>
                      <td className="px-6 py-4 text-right">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${
                            isActive
                              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-100'
                              : 'bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-200'
                          }`}
                        >
                          <ClockIcon className="h-4 w-4" />
                          {isActive ? 'In progress' : 'Completed'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
        </div>
      )}
    </div>
  )
}
