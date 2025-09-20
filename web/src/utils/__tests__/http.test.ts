import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { fetchJson, sanitizeErrorMessage, UnauthorizedError } from '../http'

const htmlError = `<!DOCTYPE html>
<html>
<head><title>502 Bad Gateway</title></head>
<body><center><h1>502 Bad Gateway</h1></center></body>
</html>`

describe('sanitizeErrorMessage', () => {
  it('returns plain text when html is provided', () => {
    expect(sanitizeErrorMessage(htmlError, 'text/html')).toBe('502 Bad Gateway')
  })

  it('returns the trimmed original message for non-html content', () => {
    expect(sanitizeErrorMessage('   Something went wrong  ')).toBe('Something went wrong')
  })
})

describe('fetchJson', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    if (!globalThis.fetch) {
      globalThis.fetch = vi.fn() as unknown as typeof fetch
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
    if (originalFetch) {
      globalThis.fetch = originalFetch
    } else {
      delete (globalThis as { fetch?: typeof fetch }).fetch
    }
  })

  it('parses successful JSON responses', async () => {
    const payload = { ok: true }
    const textSpy = vi.fn().mockResolvedValue(JSON.stringify(payload))
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      status: 200,
      statusText: 'OK',
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: textSpy,
    } as unknown as Response)

    await expect(fetchJson<typeof payload>('/api/status')).resolves.toEqual(payload)
    expect(fetchSpy).toHaveBeenCalledWith('/api/status', expect.objectContaining({
      credentials: 'include',
    }))
    expect(textSpy).toHaveBeenCalled()
  })

  it('throws UnauthorizedError for 401 responses', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      status: 401,
      statusText: 'Unauthorized',
      ok: false,
      headers: new Headers(),
      text: vi.fn(),
    } as unknown as Response)

    await expect(fetchJson('/api/status')).rejects.toBeInstanceOf(UnauthorizedError)
  })

  it('uses sanitized html error messages', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      status: 502,
      statusText: 'Bad Gateway',
      ok: false,
      headers: new Headers({ 'content-type': 'text/html' }),
      text: vi.fn().mockResolvedValue(htmlError),
    } as unknown as Response)

    await expect(fetchJson('/api/status')).rejects.toThrow('502 Bad Gateway')
  })
})
