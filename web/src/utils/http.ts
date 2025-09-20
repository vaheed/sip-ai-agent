export class UnauthorizedError extends Error {
  constructor(message = 'Authentication required') {
    super(message)
    this.name = 'UnauthorizedError'
  }
}

const isLikelyHtml = (text: string, contentType: string): boolean => {
  if (!text.trim()) {
    return false
  }

  const lowerType = contentType.toLowerCase()
  if (lowerType.includes('text/html') || lowerType.includes('application/xhtml+xml')) {
    return true
  }

  return /<[a-z!][\s\S]*>/i.test(text)
}

export const sanitizeErrorMessage = (raw: string, contentType = ''): string => {
  const text = raw.trim()
  if (!text) {
    return ''
  }

  if (!isLikelyHtml(text, contentType)) {
    return text
  }

  const titleMatch = text.match(/<title[^>]*>([^<]*)<\/title>/i)
  if (titleMatch?.[1]?.trim()) {
    return titleMatch[1].trim()
  }

  const headingMatch = text.match(/<h1[^>]*>([^<]*)<\/h1>/i)
  if (headingMatch?.[1]?.trim()) {
    return headingMatch[1].trim()
  }

  return text.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
}

const parseJson = <T>(payload: string): T => {
  const trimmed = payload.trim()
  if (!trimmed) {
    throw new Error('Empty response body')
  }
  return JSON.parse(trimmed) as T
}

export const fetchJson = async <T>(url: string, init?: RequestInit): Promise<T> => {
  const headers = new Headers(init?.headers ?? {})
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json')
  }

  const response = await fetch(url, {
    ...init,
    headers,
    credentials: init?.credentials ?? 'include',
  })

  if (response.status === 401) {
    throw new UnauthorizedError()
  }

  const contentType = response.headers.get('content-type') ?? ''
  const bodyText = await response.text()

  if (response.ok) {
    try {
      return parseJson<T>(bodyText)
    } catch {
      throw new Error('Unexpected response format')
    }
  }

  let message: string | null = null

  if (contentType.toLowerCase().includes('application/json')) {
    try {
      const payload = parseJson<Record<string, unknown>>(bodyText)
      if (payload && typeof payload === 'object') {
        const detail = payload.detail
        const error = payload.error
        if (typeof detail === 'string' && detail.trim()) {
          message = detail.trim()
        } else if (typeof error === 'string' && error.trim()) {
          message = error.trim()
        }
      }
    } catch {
      // ignore parse errors and fall back to sanitised text below
    }
  }

  if (!message) {
    const sanitized = sanitizeErrorMessage(bodyText, contentType)
    if (sanitized) {
      message = sanitized
    }
  }

  if (!message) {
    message = response.statusText || `Request failed with status ${response.status}`
  }

  throw new Error(message)
}
