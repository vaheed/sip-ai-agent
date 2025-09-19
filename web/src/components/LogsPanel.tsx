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
    <div className="relative flex h-full flex-col overflow-hidden rounded-3xl border border-slate-900/30 bg-slate-950/90 text-slate-100 shadow-xl ring-1 ring-white/10 backdrop-blur-sm dark:border-white/10">
      <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-blue-500/10 to-transparent" aria-hidden />
      <div className="relative flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3 text-sm font-semibold uppercase tracking-wide text-slate-300">
          <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-blue-500/20 text-blue-200">
            <ListBulletIcon className="h-5 w-5" />
          </span>
          Live logs
        </div>
        <span className="text-xs text-slate-500">{logs.length} entries</span>
      </div>
      <div ref={containerRef} className="relative flex-1 space-y-1 overflow-y-auto px-6 py-5 text-xs font-mono leading-relaxed">
        {logs.length === 0 ? (
          <p className="text-slate-500">No log entries yet. System output will appear here.</p>
        ) : (
          logs.map((line, index) => (
            <div key={`${index}-${line}`} className="whitespace-pre-wrap break-words text-slate-200/90">
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
