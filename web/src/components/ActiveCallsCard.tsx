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
      <div className="relative overflow-hidden rounded-3xl border border-dashed border-slate-300/80 bg-white/80 p-8 text-center shadow-sm backdrop-blur-sm dark:border-slate-700/70 dark:bg-white/5">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.12),_transparent_70%)] dark:bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_80%)]" />
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-200">
          <PhoneIcon className="h-6 w-6" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">No active calls right now.</h3>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Call cards will appear here when the agent is managing live sessions.
        </p>
      </div>
    )
  }

  return (
    <div className="relative overflow-hidden rounded-3xl border border-white/60 bg-white/80 p-6 shadow-sm backdrop-blur dark:border-white/10 dark:bg-white/5">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.12),_transparent_70%)] dark:bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.22),_transparent_85%)]" />
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-600 dark:bg-emerald-500/25 dark:text-emerald-200">
            <PhoneIcon className="h-6 w-6" />
          </div>
          <div>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">Active calls</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Monitoring {activeCallCount} ongoing session{activeCallCount === 1 ? '' : 's'}
            </p>
          </div>
        </div>
        <span className="inline-flex items-center justify-center rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-200">
          Live
        </span>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {activeHistory.map((item) => (
          <div
            key={item.call_id}
            className="rounded-2xl border border-emerald-200/70 bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 p-5 text-sm text-emerald-900 shadow-sm transition hover:border-emerald-300 dark:border-emerald-500/30 dark:from-emerald-500/20 dark:to-emerald-500/5 dark:text-emerald-100"
          >
            <div className="flex items-center justify-between text-sm font-semibold">
              <span>Call ID: {item.call_id}</span>
              <span className="text-xs uppercase tracking-wide text-emerald-600/90 dark:text-emerald-200/80">Streaming</span>
            </div>
            <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-emerald-700/90 dark:text-emerald-200/70">
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
