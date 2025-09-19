import { describe, expect, it, vi, afterEach } from 'vitest'

vi.mock('../hooks/useDashboardData', () => ({
  useDashboardData: vi.fn(),
}))

import { cleanup, render, screen } from '@testing-library/react'
import App from '../App'
import { ActiveCallsCard } from '../components/ActiveCallsCard'
import { CallHistoryTable } from '../components/CallHistoryTable'
import { LogsPanel } from '../components/LogsPanel'
import { StatusOverview } from '../components/StatusOverview'
import { useDashboardData } from '../hooks/useDashboardData'
import type { DashboardData } from '../hooks/useDashboardData'
import type { CallHistoryItem, MetricsSnapshot, StatusPayload } from '../types'

const mockedUseDashboardData = vi.mocked(useDashboardData)

const buildStatus = (overrides: Partial<StatusPayload> = {}): StatusPayload => ({
  sip_registered: true,
  active_calls: [],
  api_tokens_used: 0,
  realtime_ws_state: 'healthy',
  realtime_ws_detail: 'Stable connection',
  ...overrides,
})

const buildMetrics = (overrides: Partial<MetricsSnapshot> = {}): MetricsSnapshot => ({
  active_calls: 0,
  total_calls: 0,
  token_usage_total: 0,
  latency_seconds: {},
  register_retries: 0,
  invite_retries: 0,
  audio_pipeline_events: {},
  ...overrides,
})

const buildHistoryItem = (overrides: Partial<CallHistoryItem> = {}): CallHistoryItem => ({
  call_id: 'call-1',
  start: 1,
  end: 2,
  correlation_id: 'corr-1',
  ...overrides,
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  mockedUseDashboardData.mockReset()
  vi.clearAllMocks()
})

describe('App dashboard integration', () => {
  it('renders mocked dashboard data and updates when the hook changes', () => {
    const refresh = vi.fn<() => Promise<void>>().mockResolvedValue(undefined)

    const initialData: DashboardData = {
      status: buildStatus({ sip_registered: false, active_calls: [], api_tokens_used: 0 }),
      callHistory: [],
      logs: [],
      metrics: buildMetrics({ total_calls: 0, active_calls: 0 }),
      loading: false,
      authRequired: false,
      error: null,
      websocketState: 'connecting',
      refresh,
    }

    const updatedData: DashboardData = {
      ...initialData,
      status: buildStatus({
        sip_registered: true,
        active_calls: ['call-123'],
        api_tokens_used: 99,
        realtime_ws_state: 'healthy',
        realtime_ws_detail: 'Realtime link stable',
      }),
      callHistory: [
        buildHistoryItem({ call_id: 'call-123', start: 1704067200, end: null, correlation_id: 'live' }),
        buildHistoryItem({ call_id: 'call-456', start: 1704067000, end: 1704067060, correlation_id: 'done' }),
      ],
      logs: ['Boot sequence', 'Call connected'],
      metrics: buildMetrics({ total_calls: 5, active_calls: 1 }),
      websocketState: 'open',
    }

    mockedUseDashboardData.mockReturnValueOnce(initialData).mockReturnValueOnce(updatedData)

    const { rerender } = render(<App />)

    expect(screen.getByText('SIP AI Agent Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Not registered')).toBeInTheDocument()
    expect(screen.getByText('No log entries yet. System output will appear here.')).toBeInTheDocument()

    rerender(<App />)

    expect(screen.getByText('Registered')).toBeInTheDocument()
    expect(screen.getByText('Tokens used: 99')).toBeInTheDocument()
    expect(screen.getByText('Call ID: call-123')).toBeInTheDocument()
    expect(screen.getByText('call-456')).toBeInTheDocument()
    expect(screen.getByText('Call connected')).toBeInTheDocument()
  })
})

describe('StatusOverview', () => {
  it('renders metrics and reacts to websocket updates', () => {
    const status = buildStatus({
      sip_registered: true,
      active_calls: ['call-1', 'call-2'],
      api_tokens_used: 42,
      realtime_ws_state: 'healthy',
      realtime_ws_detail: 'Connection stable',
    })
    const metrics = buildMetrics({ total_calls: 12, active_calls: 2 })

    const { rerender } = render(
      <StatusOverview status={status} metrics={metrics} websocketState="open" />,
    )

    expect(screen.getByText('Registered')).toBeInTheDocument()
    expect(screen.getByText('Total calls')).toBeInTheDocument()
    expect(screen.getByText('Connection stable')).toBeInTheDocument()
    expect(screen.getByText('Tokens used: 42')).toBeInTheDocument()
    expect(screen.getByText('Live')).toBeInTheDocument()

    rerender(<StatusOverview status={status} metrics={metrics} websocketState="retrying" />)

    expect(screen.getByText('Reconnecting…')).toBeInTheDocument()
  })
})

describe('ActiveCallsCard', () => {
  it('shows active call details and reacts to new active calls', () => {
    const status = buildStatus({ active_calls: ['live-call'] })
    const callHistory = [
      buildHistoryItem({ call_id: 'live-call', start: 1704067190, end: null, correlation_id: 'corr-live' }),
    ]

    const { rerender } = render(<ActiveCallsCard status={status} callHistory={callHistory} />)

    expect(screen.getByText('Active calls')).toBeInTheDocument()
    expect(screen.getByText('Call ID: live-call')).toBeInTheDocument()
    expect(screen.getByText('Live')).toBeInTheDocument()
    expect(screen.getByText(/Monitoring 1 ongoing session/)).toBeInTheDocument()

    const updatedStatus = buildStatus({ active_calls: ['live-call', 'second-call'] })
    const updatedHistory = [
      ...callHistory,
      buildHistoryItem({ call_id: 'second-call', start: 1704067250, end: null, correlation_id: 'corr-second' }),
    ]

    rerender(<ActiveCallsCard status={updatedStatus} callHistory={updatedHistory} />)

    expect(screen.getByText(/Monitoring 2 ongoing sessions/)).toBeInTheDocument()
    expect(screen.getByText('Call ID: second-call')).toBeInTheDocument()
  })

  it('renders the empty state when no calls are active', () => {
    const status = buildStatus({ active_calls: [] })
    const callHistory: CallHistoryItem[] = []

    render(<ActiveCallsCard status={status} callHistory={callHistory} />)

    expect(screen.getByText('No active calls right now.')).toBeInTheDocument()
  })
})

describe('LogsPanel', () => {
  it('lists log entries and updates counts', () => {
    const { rerender } = render(<LogsPanel logs={['first event']} />)

    expect(screen.getByText('1 entries')).toBeInTheDocument()
    expect(screen.getByText('first event')).toBeInTheDocument()

    rerender(<LogsPanel logs={['first event', 'second event', 'third event']} />)

    expect(screen.getByText('3 entries')).toBeInTheDocument()
    expect(screen.getByText('third event')).toBeInTheDocument()
  })
})

describe('CallHistoryTable', () => {
  it('renders an empty state when no history is available', () => {
    render(<CallHistoryTable history={[]} />)

    expect(
      screen.getByText('Call history will appear once calls are completed.'),
    ).toBeInTheDocument()
  })

  it('lists call rows with their status', () => {
    const history: CallHistoryItem[] = [
      buildHistoryItem({ call_id: 'call-completed', start: 1704067200, end: 1704067260, correlation_id: 'corr-123' }),
      buildHistoryItem({ call_id: 'call-active', start: 1704067300, end: null, correlation_id: null }),
    ]

    render(<CallHistoryTable history={history} />)

    expect(screen.getByRole('link', { name: /download csv/i })).toHaveAttribute('href', '/api/call_history.csv')
    expect(screen.getByText('call-completed')).toBeInTheDocument()
    expect(screen.getByText('corr-123')).toBeInTheDocument()
    expect(screen.getAllByText('Completed')).toHaveLength(1)
    expect(screen.getByText('call-active')).toBeInTheDocument()
    expect(screen.getAllByText('In progress')).toHaveLength(1)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })
})
