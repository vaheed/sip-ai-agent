import { expect, test } from '@playwright/test'

import type { CallHistoryItem, MetricsSnapshot, StatusPayload } from '../../src/types'

type DashboardFixtures = {
  status: StatusPayload
  callHistory: CallHistoryItem[]
  logs: { logs: string[] }
  metrics: MetricsSnapshot
}

const createFixtures = (): DashboardFixtures => {
  const now = Math.floor(Date.now() / 1000)
  return {
    status: {
      sip_registered: true,
      active_calls: ['call-1'],
      api_tokens_used: 1234,
      realtime_ws_state: 'healthy',
      realtime_ws_detail: 'Realtime channel healthy',
    },
    callHistory: [
      {
        call_id: 'call-1',
        start: now - 120,
        end: null,
        correlation_id: 'corr-42',
      },
      {
        call_id: 'call-0',
        start: now - 600,
        end: now - 420,
        correlation_id: null,
      },
    ],
    logs: {
      logs: ['2024-02-01T12:00:00Z INFO Connected to upstream services'],
    },
    metrics: {
      active_calls: 1,
      total_calls: 58,
      token_usage_total: 9876,
      latency_seconds: {
        invite: 0.42,
        register: 0.31,
      },
      register_retries: 0,
      invite_retries: 1,
      audio_pipeline_events: {
        packets_streamed: 12_345,
      },
    },
  }
}

let fixtures: DashboardFixtures

test.beforeEach(async ({ page }) => {
  fixtures = createFixtures()

  await page.addInitScript(() => {
    type EventLike = { type: string }
    type MessageEventLike = { data: unknown }

    class MockWebSocket {
      public static OPEN = 1
      public static CLOSED = 3
      public readyState = MockWebSocket.OPEN
      public url: string
      public onopen: ((event: EventLike) => void) | null = null
      public onclose: ((event: EventLike) => void) | null = null
      public onerror: ((event: EventLike) => void) | null = null
      public onmessage: ((event: MessageEventLike) => void) | null = null

      constructor(url: string) {
        this.url = url
        setTimeout(() => {
          this.onopen?.({ type: 'open' })
        }, 0)
      }

      send() {}

      close() {
        this.readyState = MockWebSocket.CLOSED
        this.onclose?.({ type: 'close' })
      }

      addEventListener(type: string, listener: (...args: unknown[]) => void) {
        switch (type) {
          case 'open':
            this.onopen = listener as (event: EventLike) => void
            break
          case 'close':
            this.onclose = listener as (event: EventLike) => void
            break
          case 'error':
            this.onerror = listener as (event: EventLike) => void
            break
          case 'message':
            this.onmessage = listener as (event: MessageEventLike) => void
            break
          default:
            break
        }
      }

      removeEventListener(type: string) {
        if (type === 'open') this.onopen = null
        if (type === 'close') this.onclose = null
        if (type === 'error') this.onerror = null
        if (type === 'message') this.onmessage = null
      }
    }

    const globalAny = globalThis as Record<string, unknown>
    globalAny.WebSocket = MockWebSocket
  })

  await page.route('**/api/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(fixtures.status),
    })
  })

  await page.route('**/api/call_history', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(fixtures.callHistory),
    })
  })

  await page.route('**/api/logs', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(fixtures.logs),
    })
  })

  await page.route('**/metrics', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(fixtures.metrics),
    })
  })
})

test('renders dashboard data and environment notice', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { level: 1, name: 'SIP AI Agent Dashboard' })).toBeVisible()
  await expect(page.getByText('SIP registration')).toBeVisible()
  await expect(page.getByText('Registered')).toBeVisible()
  await expect(page.getByText('Call ID: call-1')).toBeVisible()
  await expect(page.getByRole('heading', { level: 2, name: 'Call History' })).toBeVisible()
  await expect(page.getByText('Monitoring 1 ongoing session')).toBeVisible()

  await expect(page.getByText('Environment-managed configuration')).toBeVisible()
  await expect(page.getByText('Runtime settings are now sourced exclusively from the .env file.')).toBeVisible()
})
