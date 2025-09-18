import { useEffect, useRef } from 'react'
import { ListBulletIcon } from '@heroicons/react/24/outline'

interface LogsPanelProps {
  logs: string[]
}

export const LogsPanel = ({ logs }: LogsPanelProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [logs])

  return (
    <div className="flex h-full flex-col rounded-2xl border border-border-light bg-gray-950 text-gray-100 shadow-sm dark:border-gray-800">
      <div className="flex items-center justify-between border-b border-border-light/40 px-4 py-3 dark:border-gray-800">
        <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-400">
          <ListBulletIcon className="h-5 w-5" />
          Live logs
        </div>
        <span className="text-xs text-gray-500">{logs.length} entries</span>
      </div>
      <div ref={containerRef} className="flex-1 space-y-1 overflow-y-auto bg-black/20 p-4 text-xs font-mono leading-relaxed">
        {logs.length === 0 ? (
          <p className="text-gray-500">No log entries yet. System output will appear here.</p>
        ) : (
          logs.map((line, index) => (
            <div key={`${index}-${line}`} className="whitespace-pre-wrap break-words text-gray-200">
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
