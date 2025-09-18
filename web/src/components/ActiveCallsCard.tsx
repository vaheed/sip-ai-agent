import { useEffect, useMemo, useState } from 'react'
import { PhoneIcon } from '@heroicons/react/24/outline'

import type { CallHistoryItem, StatusPayload } from '../types'
import { formatDuration, formatTimestamp } from '../utils/time'

interface ActiveCallsCardProps {
  status: StatusPayload | null
  callHistory: CallHistoryItem[]
}

export const ActiveCallsCard = ({ status, callHistory }: ActiveCallsCardProps) => {
  const [now, setNow] = useState(() => Date.now() / 1000)

  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now() / 1000), 1000)
    return () => window.clearInterval(interval)
  }, [])

  const activeHistory = useMemo(() => {
    const historyMap = new Map<string, CallHistoryItem>()
    for (const item of callHistory) {
      if (item.end === null) {
        historyMap.set(item.call_id, item)
      }
    }
    const activeIds = status?.active_calls ?? []
    return activeIds.map((id) => historyMap.get(id)).filter(Boolean) as CallHistoryItem[]
  }, [callHistory, status?.active_calls])

  const activeCallCount = status?.active_calls?.length ?? 0

  if (activeCallCount === 0) {
    return (
      <div className="h-full rounded-2xl border border-dashed border-gray-300 bg-white/40 p-6 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-400">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
          <PhoneIcon className="h-6 w-6" />
        </div>
        <p>No active calls right now.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4 rounded-2xl border border-border-light bg-white/70 p-6 shadow-sm backdrop-blur dark:border-border-dark dark:bg-gray-900/70">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200">
            <PhoneIcon className="h-6 w-6" />
          </div>
          <div>
            <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">Active calls</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Monitoring {activeCallCount} ongoing session{activeCallCount === 1 ? '' : 's'}
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {activeHistory.map((item) => (
          <div
            key={item.call_id}
            className="flex flex-col gap-1 rounded-xl border border-emerald-200/70 bg-emerald-50/80 p-4 text-sm text-emerald-800 shadow-sm transition hover:border-emerald-300 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200"
          >
            <div className="flex items-center justify-between text-sm font-medium">
              <span>Call ID: {item.call_id}</span>
              <span className="text-xs uppercase tracking-wide text-emerald-700/80 dark:text-emerald-300/80">Live</span>
            </div>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-emerald-700/80 dark:text-emerald-300/80">
              <span>Started {formatTimestamp(item.start)}</span>
              <span>Elapsed {formatDuration(item.start, null, now)}</span>
              {item.correlation_id ? <span>Correlation {item.correlation_id}</span> : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
