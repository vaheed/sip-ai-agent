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

const toneStyles: Record<
  Tone,
  {
    container: string
    icon: string
    value: string
    description: string
  }
> = {
  default: {
    container:
      'border-slate-200/80 bg-white/80 text-slate-900 dark:border-white/10 dark:bg-white/5 dark:text-slate-100',
    icon: 'bg-slate-900/5 text-slate-700 dark:bg-white/10 dark:text-slate-200',
    value: 'text-slate-900 dark:text-slate-100',
    description: 'text-slate-500 dark:text-slate-400',
  },
  success: {
    container:
      'border-emerald-200/80 bg-emerald-50/80 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100',
    icon: 'bg-emerald-500/15 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-100',
    value: 'text-emerald-700 dark:text-emerald-100',
    description: 'text-emerald-600 dark:text-emerald-200/80',
  },
  danger: {
    container:
      'border-rose-200/80 bg-rose-50/80 text-rose-800 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100',
    icon: 'bg-rose-500/15 text-rose-600 dark:bg-rose-500/20 dark:text-rose-100',
    value: 'text-rose-700 dark:text-rose-100',
    description: 'text-rose-600 dark:text-rose-200/80',
  },
  warning: {
    container:
      'border-amber-200/80 bg-amber-50/80 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100',
    icon: 'bg-amber-500/15 text-amber-600 dark:bg-amber-500/20 dark:text-amber-100',
    value: 'text-amber-700 dark:text-amber-100',
    description: 'text-amber-600 dark:text-amber-200/80',
  },
}

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
  const styles = toneStyles[tone]

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border p-5 shadow-sm backdrop-blur-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-md ${styles.container}`}
    >
      <div className="absolute -right-6 top-6 h-24 w-24 rounded-full bg-white/10 opacity-0 transition-opacity duration-200 group-hover:opacity-100 dark:bg-white/10" />
      <div className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${styles.icon}`}>
        <Icon className="h-6 w-6" />
      </div>
      <div className="mt-4 space-y-1">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500/80 dark:text-slate-400/80">{title}</p>
        <p className={`text-2xl font-semibold leading-tight ${styles.value}`}>{value}</p>
        {description ? <p className={`text-xs ${styles.description}`}>{description}</p> : null}
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

  const realtimeTone: Tone = sipRegistered
    ? realtimeState === 'healthy'
      ? 'success'
      : realtimeState === 'unhealthy'
        ? 'danger'
        : 'warning'
    : 'warning'

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
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
        value={
          realtimeState === 'healthy'
            ? 'Healthy'
            : realtimeState === 'unhealthy'
              ? 'Unhealthy'
              : realtimeState
        }
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
