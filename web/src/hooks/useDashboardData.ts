import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type {
  CallHistoryItem,
  ConfigMap,
  DashboardEvent,
  MetricsSnapshot,
  StatusPayload,
} from '../types'

class UnauthorizedError extends Error {
  constructor(message = 'Authentication required') {
    super(message)
    this.name = 'UnauthorizedError'
  }
}

const fetchJson = async <T>(url: string): Promise<T> => {
  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  })

  if (response.status === 401) {
    throw new UnauthorizedError()
  }

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || response.statusText)
  }

  return response.json() as Promise<T>
}

const updateConfigRequest = async (payload: ConfigMap): Promise<void> => {
  const response = await fetch('/api/update_config', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (response.status === 401) {
    throw new UnauthorizedError()
  }

  const data = await response.json().catch(() => ({ success: response.ok }))
  if (!response.ok || !data.success) {
    const detail = data?.error || response.statusText
    throw new Error(detail || 'Failed to update configuration')
  }
}

export interface DashboardData {
  status: StatusPayload | null
  callHistory: CallHistoryItem[]
  logs: string[]
  metrics: MetricsSnapshot | null
  config: ConfigMap
  loading: boolean
  authRequired: boolean
  error: string | null
  websocketState: 'connecting' | 'open' | 'retrying' | 'closed'
  refresh: () => Promise<void>
  saveConfig: (values: ConfigMap) => Promise<void>
}

export const useDashboardData = (): DashboardData => {
  const [status, setStatus] = useState<StatusPayload | null>(null)
  const [callHistory, setCallHistory] = useState<CallHistoryItem[]>([])
  const [logs, setLogs] = useState<string[]>([])
  const [metrics, setMetrics] = useState<MetricsSnapshot | null>(null)
  const [config, setConfig] = useState<ConfigMap>({})
  const [loading, setLoading] = useState(true)
  const [authRequired, setAuthRequired] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [websocketState, setWebsocketState] = useState<'connecting' | 'open' | 'retrying' | 'closed'>(
    'connecting',
  )

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<number | null>(null)

  const closeWebSocket = useCallback(() => {
    if (reconnectTimer.current) {
      window.clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setWebsocketState('closed')
  }, [])

  const handleUnauthorized = useCallback(
    (err: unknown) => {
      if (err instanceof UnauthorizedError) {
        setAuthRequired(true)
        closeWebSocket()
        setLoading(false)
        return true
      }
      return false
    },
    [closeWebSocket],
  )

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [statusPayload, historyPayload, logsPayload, configPayload, metricsPayload] =
        await Promise.all([
          fetchJson<StatusPayload>('/api/status'),
          fetchJson<CallHistoryItem[]>('/api/call_history'),
          fetchJson<{ logs: string[] }>('/api/logs'),
          fetchJson<ConfigMap>('/api/config'),
          fetchJson<MetricsSnapshot>('/metrics').catch(() => null),
        ])

      setStatus(statusPayload)
      setCallHistory(historyPayload)
      setLogs(logsPayload.logs ?? [])
      if (configPayload) {
        setConfig(configPayload)
      }
      if (metricsPayload) {
        setMetrics(metricsPayload)
      }
      setError(null)
      setAuthRequired(false)
    } catch (err) {
      if (handleUnauthorized(err)) {
        return
      }
      console.error('Failed to load dashboard data', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [handleUnauthorized])

  const saveConfig = useCallback(
    async (values: ConfigMap) => {
      try {
        await updateConfigRequest(values)
        await refresh()
      } catch (err) {
        if (handleUnauthorized(err)) {
          throw err
        }
        throw err instanceof Error ? err : new Error('Failed to update configuration')
      }
    },
    [handleUnauthorized, refresh],
  )

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    if (authRequired) {
      return
    }

    let cancelled = false

    const connect = (retryDelay = 0) => {
      if (cancelled) {
        return
      }
      if (reconnectTimer.current) {
        window.clearTimeout(reconnectTimer.current)
      }

      if (retryDelay > 0) {
        setWebsocketState('retrying')
      } else {
        setWebsocketState('connecting')
      }

      reconnectTimer.current = window.setTimeout(() => {
        try {
          const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
          const wsUrl = `${protocol}://${window.location.host}/ws/events`
          const ws = new WebSocket(wsUrl)
          wsRef.current = ws

          ws.onopen = () => {
            setWebsocketState('open')
          }

          ws.onmessage = (event) => {
            try {
              const data: DashboardEvent = JSON.parse(event.data)
              switch (data.type) {
                case 'status':
                  setStatus(data.payload)
                  break
                case 'call_history':
                  setCallHistory(data.payload)
                  break
                case 'metrics':
                  setMetrics(data.payload)
                  break
                case 'logs':
                  setLogs(data.entries ?? [])
                  break
                case 'log':
                  setLogs((prev) => {
                    const next = [...prev, data.entry]
                    return next.slice(-200)
                  })
                  break
                default:
                  break
              }
            } catch (err) {
              console.error('Failed to parse websocket message', err)
            }
          }

          ws.onclose = () => {
            if (cancelled) {
              return
            }
            setWebsocketState('retrying')
            reconnectTimer.current = window.setTimeout(() => connect(Math.min(retryDelay * 2 || 1000, 10000)), 1000)
          }

          ws.onerror = () => {
            ws.close()
          }
        } catch (err) {
          console.error('WebSocket connection error', err)
          reconnectTimer.current = window.setTimeout(() => connect(Math.min(retryDelay * 2 || 1000, 10000)), 2000)
        }
      }, retryDelay)
    }

    connect()

    return () => {
      cancelled = true
      closeWebSocket()
    }
  }, [authRequired, closeWebSocket])

  const sortedHistory = useMemo(() => {
    return [...callHistory].sort((a, b) => b.start - a.start)
  }, [callHistory])

  return {
    status,
    callHistory: sortedHistory,
    logs,
    metrics,
    config,
    loading,
    authRequired,
    error,
    websocketState,
    refresh,
    saveConfig,
  }
}
