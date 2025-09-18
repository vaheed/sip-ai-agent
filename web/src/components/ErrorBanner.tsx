import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface ErrorBannerProps {
  message: string
  onRetry?: () => void
}

export const ErrorBanner = ({ message, onRetry }: ErrorBannerProps) => {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-rose-200 bg-rose-50/80 px-4 py-3 text-sm text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200">
      <div className="flex items-center gap-2">
        <ExclamationTriangleIcon className="h-5 w-5" />
        <span>{message}</span>
      </div>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-full border border-rose-300 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-rose-700 transition hover:bg-rose-100 dark:border-rose-700 dark:text-rose-200 dark:hover:bg-rose-900/40"
        >
          Retry
        </button>
      ) : null}
    </div>
  )
}
