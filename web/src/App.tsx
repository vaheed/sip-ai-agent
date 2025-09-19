import { ThemeProvider } from './theme-provider'
import { ActiveCallsCard } from './components/ActiveCallsCard'
import { AuthNotice } from './components/AuthNotice'
import { CallHistoryTable } from './components/CallHistoryTable'
import { ErrorBanner } from './components/ErrorBanner'
import { LoadingScreen } from './components/LoadingScreen'
import { LogsPanel } from './components/LogsPanel'
import { StatusOverview } from './components/StatusOverview'
import { ThemeToggle } from './components/ThemeToggle'
import { useDashboardData } from './hooks/useDashboardData'

const DashboardView = () => {
  const {
    status,
    callHistory,
    logs,
    metrics,
    loading,
    authRequired,
    error,
    websocketState,
    refresh,
  } = useDashboardData()

  if (authRequired) {
    return <AuthNotice />
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-100 pb-16 pt-10 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-[-140px] h-[420px] w-[720px] -translate-x-1/2 rounded-full bg-blue-400/25 blur-[140px] dark:bg-blue-500/15" />
        <div className="absolute -right-40 bottom-[-120px] h-[360px] w-[360px] rounded-full bg-emerald-300/30 blur-[140px] dark:bg-emerald-500/10" />
        <div className="absolute -left-32 bottom-20 h-64 w-64 rounded-full bg-indigo-300/20 blur-[120px] dark:bg-indigo-500/10" />
      </div>

      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 sm:px-6 lg:px-8">
        <header className="relative overflow-hidden rounded-3xl border border-white/60 bg-white/80 px-6 py-8 shadow-xl backdrop-blur dark:border-white/10 dark:bg-white/5 sm:px-10">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),_transparent_65%)] dark:bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.22),_transparent_70%)]" />
          <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
            <div className="max-w-2xl space-y-4">
              <span className="inline-flex items-center gap-2 rounded-full bg-blue-600/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-600 dark:text-blue-300">
                Realtime operations
              </span>
              <div className="space-y-3">
                <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">SIP AI Agent Dashboard</h1>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  Monitor SIP connectivity, live calls, and system telemetry. Save configuration changes safely and stay on top of WebSocket health in one unified workspace.
                </p>
              </div>
              <div className="flex flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-900/5 px-3 py-1 dark:bg-white/5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden />
                  Status insights auto-refresh
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-900/5 px-3 py-1 dark:bg-white/5">
                  <span className="h-2 w-2 rounded-full bg-blue-500" aria-hidden />
                  Environment-managed config
                </span>
              </div>
            </div>
            <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center sm:justify-end md:w-auto md:flex-col">
              <ThemeToggle />
              <button
                type="button"
                onClick={refresh}
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300 dark:bg-blue-500 dark:hover:bg-blue-400"
              >
                {loading ? 'Refreshing…' : 'Refresh data'}
              </button>
            </div>
          </div>
        </header>

        {error ? <ErrorBanner message={error} onRetry={refresh} /> : null}

        {loading ? (
          <LoadingScreen />
        ) : (
          <main className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_340px]">
            <section className="space-y-8">
              <StatusOverview status={status} metrics={metrics} websocketState={websocketState} />
              <ActiveCallsCard status={status} callHistory={callHistory} />
              <CallHistoryTable history={callHistory} />
              <div className="relative overflow-hidden rounded-3xl border border-white/60 bg-white/80 p-6 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-white/5 sm:p-8">
                <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.12),_transparent_75%)] dark:bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),_transparent_80%)]" />
                <div className="space-y-4 text-sm text-slate-600 dark:text-slate-300">
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Environment-managed configuration</h2>
                  <p>
                    Runtime settings are now sourced exclusively from the <code>.env</code> file. Update SIP credentials,
                    OpenAI keys, and feature toggles directly in that file and restart the containers to apply the
                    changes.
                  </p>
                  <p>
                    Monitor authentication credentials are also provided via the environment. Set{' '}
                    <code>MONITOR_ADMIN_USERNAME</code> and <code>MONITOR_ADMIN_PASSWORD</code> to control dashboard
                    access.
                  </p>
                </div>
              </div>
            </section>
            <aside className="space-y-8 xl:sticky xl:top-24">
              <LogsPanel logs={logs} />
            </aside>
          </main>
        )}
      </div>
    </div>
  )
}

const App = () => {
  return (
    <ThemeProvider>
      <DashboardView />
    </ThemeProvider>
  )
}

export default App
