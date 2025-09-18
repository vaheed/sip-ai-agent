import { SparklesIcon } from '@heroicons/react/24/outline'

export const LoadingScreen = () => {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <div className="animate-spin rounded-full border-4 border-blue-200 border-t-blue-600 p-4">
        <SparklesIcon className="h-10 w-10 text-blue-600 dark:text-blue-300" />
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">Loading dashboard data…</p>
    </div>
  )
}
