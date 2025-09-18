import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PhoneArrowDownLeftIcon,
  SignalIcon,
  WifiIcon,
} from '@heroicons/react/24/outline'

import type { MetricsSnapshot, StatusPayload } from '../types'

interface StatusOverviewProps {
  status: StatusPayload | null
  metrics: MetricsSnapshot | null
  websocketState: 'connecting' | 'open' | 'retrying' | 'closed'
}

type Tone = 'default' | 'success' | 'danger' | 'warning'

const StatCard = ({
  icon: Icon,
  title,
  value,
  description,
  tone = 'default',
}: {
  icon: typeof CheckCircleIcon
  title: string
  value: string
  description?: string
  tone?: Tone
}) => {
  const base =
    'flex items-center gap-4 rounded-2xl border border-border-light bg-white/70 p-4 shadow-sm backdrop-blur dark:border-border-dark dark:bg-gray-900/70'
  const toneClasses: Record<Tone, string> = {
    default: '',
    success: 'border-emerald-200 bg-emerald-50/80 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/50 dark:text-emerald-300',
    danger: 'border-rose-200 bg-rose-50/80 text-rose-700 dark:border-rose-900/70 dark:bg-rose-950/50 dark:text-rose-300',
    warning:
      'border-amber-200 bg-amber-50/80 text-amber-700 dark:border-amber-900/70 dark:bg-amber-950/50 dark:text-amber-200',
  }

  return (
    <div className={`${base} ${toneClasses[tone]}`}>
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/60 shadow-inner dark:bg-gray-800/60">
        <Icon className="h-6 w-6" />
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{value}</p>
        {description ? (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{description}</p>
        ) : null}
      </div>
    </div>
  )
}

export const StatusOverview = ({ status, metrics, websocketState }: StatusOverviewProps) => {
  const sipRegistered = status?.sip_registered ?? false
  const activeCalls = status?.active_calls?.length ?? 0
  const tokens = status?.api_tokens_used ?? 0
  const realtimeState = status?.realtime_ws_state ?? 'unknown'
  const realtimeDetail = status?.realtime_ws_detail ?? ''

  const realtimeDescription = realtimeDetail ? realtimeDetail : 'Live audio/LLM websocket status'

  const websocketValueMap: Record<StatusOverviewProps['websocketState'], string> = {
    connecting: 'Connecting…',
    open: 'Live',
    retrying: 'Reconnecting…',
    closed: 'Offline',
  }

  const realtimeTone: 'success' | 'danger' | 'warning' | 'default' = sipRegistered
    ? realtimeState === 'healthy'
      ? 'success'
      : realtimeState === 'unhealthy'
        ? 'danger'
        : 'warning'
    : 'warning'

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <StatCard
        icon={sipRegistered ? CheckCircleIcon : ExclamationTriangleIcon}
        title="SIP registration"
        value={sipRegistered ? 'Registered' : 'Not registered'}
        description={`${activeCalls} active call${activeCalls === 1 ? '' : 's'}`}
        tone={sipRegistered ? 'success' : 'danger'}
      />
      <StatCard
        icon={PhoneArrowDownLeftIcon}
        title="Total calls"
        value={metrics ? metrics.total_calls.toString() : '–'}
        description={`Current sessions: ${activeCalls}`}
      />
      <StatCard
        icon={SignalIcon}
        title="Realtime channel"
        value={realtimeState === 'healthy' ? 'Healthy' : realtimeState === 'unhealthy' ? 'Unhealthy' : realtimeState}
        description={realtimeDescription}
        tone={realtimeTone}
      />
      <StatCard
        icon={WifiIcon}
        title="WebSocket link"
        value={websocketValueMap[websocketState]}
        description={`Tokens used: ${tokens}`}
        tone={websocketState === 'open' ? 'success' : websocketState === 'retrying' ? 'warning' : 'default'}
      />
    </div>
  )
}
