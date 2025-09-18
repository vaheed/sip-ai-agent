import { expect, test } from '@playwright/test'

import type { CallHistoryItem, MetricsSnapshot, StatusPayload } from '../../src/types'

type DashboardFixtures = {
  status: StatusPayload
  callHistory: CallHistoryItem[]
  logs: { logs: string[] }
  config: Record<string, string>
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
    config: {
      SIP_DOMAIN: 'pbx.example.com',
      SIP_USER: '1001',
      SIP_PASS: 'secret',
      OPENAI_API_KEY: 'test-key',
      AGENT_ID: 'demo-agent',
      ENABLE_SIP: 'true',
      ENABLE_AUDIO: 'true',
      OPENAI_MODE: 'realtime',
      OPENAI_MODEL: 'gpt-4o-realtime-preview',
      OPENAI_VOICE: 'verse',
      OPENAI_TEMPERATURE: '0.8',
      SYSTEM_PROMPT: 'Hello world',
      SIP_TRANSPORT_PORT: '5060',
      SIP_JB_MIN: '200',
      SIP_JB_MAX: '400',
      SIP_JB_MAX_PRE: '800',
      SIP_ENABLE_ICE: 'true',
      SIP_ENABLE_TURN: 'false',
      SIP_STUN_SERVER: 'stun:stun.example.com',
      SIP_TURN_SERVER: '',
      SIP_TURN_USER: '',
      SIP_TURN_PASS: '',
      SIP_ENABLE_SRTP: 'false',
      SIP_SRTP_OPTIONAL: 'false',
      SIP_PREFERRED_CODECS: 'opus,pcmu',
      SIP_REG_RETRY_BASE: '1',
      SIP_REG_RETRY_MAX: '32',
      SIP_INVITE_RETRY_BASE: '1',
      SIP_INVITE_RETRY_MAX: '16',
      SIP_INVITE_MAX_ATTEMPTS: '4',
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

  await page.route('**/api/config', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(fixtures.config),
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

test('renders dashboard data and saves configuration updates', async ({ page }) => {
  let savedConfig: Record<string, string> | undefined

  await page.route('**/api/update_config', async (route) => {
    savedConfig = route.request().postDataJSON() as Record<string, string>
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        reload: {
          status: 'restarting',
          active_calls: 0,
          message: 'Restarting now',
        },
      }),
    })
  })

  await page.goto('/')

  await expect(page.getByRole('heading', { level: 1, name: 'SIP AI Agent Dashboard' })).toBeVisible()
  await expect(page.getByText('SIP registration')).toBeVisible()
  await expect(page.getByText('Registered')).toBeVisible()
  await expect(page.getByText('Call ID: call-1')).toBeVisible()
  await expect(page.getByRole('heading', { level: 2, name: 'Call History' })).toBeVisible()
  await expect(page.getByText('Monitoring 1 ongoing session')).toBeVisible()

  const sipDomainField = page.getByLabel('SIP_DOMAIN')
  await expect(sipDomainField).toHaveValue(fixtures.config.SIP_DOMAIN)

  await sipDomainField.fill('sip.internal.example.com')
  await page.getByRole('button', { name: 'Save changes' }).click()

  await expect(page.getByText('Restarting now', { exact: true })).toBeVisible()
  expect(savedConfig?.SIP_DOMAIN).toBe('sip.internal.example.com')
})
