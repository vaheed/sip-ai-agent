export interface StatusPayload {
  sip_registered: boolean
  active_calls: string[]
  api_tokens_used: number
  realtime_ws_state: string
  realtime_ws_detail?: string | null
}

export interface CallHistoryItem {
  call_id: string
  start: number
  end: number | null
  correlation_id?: string | null
}

export interface MetricsSnapshot {
  active_calls: number
  total_calls: number
  token_usage_total: number
  latency_seconds: Record<string, number>
  register_retries: number
  invite_retries: number
  audio_pipeline_events: Record<string, number>
}

export type ConfigMap = Record<string, string>

export type ReloadState = 'restarting' | 'waiting_for_calls' | 'noop' | 'error'

export interface ReloadStatus {
  status: ReloadState
  active_calls: number
  message: string
  error?: string
}

export interface ConfigUpdateResponse {
  success: boolean
  reload?: ReloadStatus | null
}

export type DashboardEvent =
  | { type: 'status'; payload: StatusPayload }
  | { type: 'call_history'; payload: CallHistoryItem[] }
  | { type: 'metrics'; payload: MetricsSnapshot }
  | { type: 'logs'; entries: string[] }
  | { type: 'log'; entry: string }

export interface DashboardState {
  status: StatusPayload | null
  callHistory: CallHistoryItem[]
  logs: string[]
  metrics: MetricsSnapshot | null
  config: ConfigMap
}
