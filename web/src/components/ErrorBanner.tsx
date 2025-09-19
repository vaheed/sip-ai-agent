import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface ErrorBannerProps {
  message: string
  onRetry?: () => void
}

export const ErrorBanner = ({ message, onRetry }: ErrorBannerProps) => {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-rose-200/80 bg-rose-50/90 px-4 py-3 text-sm text-rose-700 shadow-sm dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-rose-500/20 text-rose-600 dark:bg-rose-500/30 dark:text-rose-100">
          <ExclamationTriangleIcon className="h-5 w-5" />
        </span>
        <span className="leading-snug">{message}</span>
      </div>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center justify-center rounded-full border border-rose-300 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-rose-700 transition hover:bg-rose-100 dark:border-rose-400/60 dark:text-rose-100 dark:hover:bg-rose-500/20"
        >
          Retry
        </button>
      ) : null}
    </div>
  )
}
