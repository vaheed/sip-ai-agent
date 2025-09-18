import { ClockIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

import type { CallHistoryItem } from '../types'
import { formatDuration, formatTimestamp } from '../utils/time'

interface CallHistoryTableProps {
  history: CallHistoryItem[]
}

export const CallHistoryTable = ({ history }: CallHistoryTableProps) => {
  if (history.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-gray-300 bg-white/60 p-6 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-900/50 dark:text-gray-400">
        <DocumentTextIcon className="h-8 w-8" />
        <p>Call history will appear once calls are completed.</p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-border-light bg-white/80 shadow-sm dark:border-border-dark dark:bg-gray-900/70">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
          <thead className="bg-gray-50/80 text-left text-xs uppercase tracking-wide text-gray-500 dark:bg-gray-800/60 dark:text-gray-400">
            <tr>
              <th className="px-4 py-3">Call ID</th>
              <th className="px-4 py-3">Correlation</th>
              <th className="px-4 py-3">Started</th>
              <th className="px-4 py-3">Ended</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-sm text-gray-700 dark:divide-gray-800 dark:text-gray-200">
            {history.map((item) => {
              const isActive = item.end === null
              return (
                <tr key={`${item.call_id}-${item.start}`} className="hover:bg-gray-50/60 dark:hover:bg-gray-800/40">
                  <td className="whitespace-nowrap px-4 py-3 font-medium">{item.call_id}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
                    {item.correlation_id ?? '—'}
                  </td>
                  <td className="px-4 py-3">{formatTimestamp(item.start)}</td>
                  <td className="px-4 py-3">{formatTimestamp(item.end ?? undefined)}</td>
                  <td className="px-4 py-3 text-sm">{formatDuration(item.start, item.end)}</td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${
                        isActive
                          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-800/60 dark:text-gray-300'
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
    </div>
  )
}
