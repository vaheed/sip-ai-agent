import { ThemeProvider } from './theme-provider'
import { ActiveCallsCard } from './components/ActiveCallsCard'
import { AuthNotice } from './components/AuthNotice'
import { CallHistoryTable } from './components/CallHistoryTable'
import { ConfigEditor } from './components/ConfigEditor'
import { ErrorBanner } from './components/ErrorBanner'
import { LoadingScreen } from './components/LoadingScreen'
import { LogsPanel } from './components/LogsPanel'
import { StatusOverview } from './components/StatusOverview'
import { ThemeToggle } from './components/ThemeToggle'
import { useDashboardData } from './hooks/useDashboardData'

const DashboardView = () => {
  const { status, callHistory, logs, metrics, config, loading, authRequired, error, websocketState, refresh, saveConfig } =
    useDashboardData()

  if (authRequired) {
    return <AuthNotice />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-slate-200 pb-16 pt-10 dark:from-slate-950 dark:via-slate-900 dark:to-black">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-50">SIP AI Agent Dashboard</h1>
            <p className="mt-2 max-w-2xl text-sm text-gray-600 dark:text-gray-400">
              Monitor SIP connectivity, live calls, and system logs in real time. Update configuration safely when needed.
            </p>
          </div>
          <ThemeToggle />
        </header>

        {error ? <ErrorBanner message={error} onRetry={refresh} /> : null}

        {loading ? (
          <LoadingScreen />
        ) : (
          <div className="flex flex-col gap-8">
            <StatusOverview status={status} metrics={metrics} websocketState={websocketState} />

            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2 space-y-6">
                <ActiveCallsCard status={status} callHistory={callHistory} />
                <CallHistoryTable history={callHistory} />
                <ConfigEditor config={config} onSave={saveConfig} />
              </div>
              <div className="flex flex-col gap-6">
                <LogsPanel logs={logs} />
              </div>
            </div>
          </div>
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
