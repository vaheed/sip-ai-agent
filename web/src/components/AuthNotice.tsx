import { LockClosedIcon } from '@heroicons/react/24/outline'

export const AuthNotice = () => {
  return (
    <div className="mx-auto mt-24 max-w-lg rounded-3xl border border-dashed border-gray-300 bg-white/80 p-10 text-center shadow-lg dark:border-gray-700 dark:bg-gray-900/70">
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300">
        <LockClosedIcon className="h-8 w-8" />
      </div>
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Administrator sign-in required</h2>
      <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">
        Your session has expired or you are not signed in. Please authenticate to access the monitoring dashboard.
      </p>
      <a
        href="/login?next=/dashboard"
        className="mt-6 inline-flex items-center justify-center rounded-full bg-blue-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500"
      >
        Go to login
      </a>
    </div>
  )
}
