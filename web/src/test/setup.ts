import '@testing-library/jest-dom/vitest'

// Provide a minimal resizeObserver mock for components relying on layout measurements.
class ResizeObserverMock implements ResizeObserver {
  callback: ResizeObserverCallback
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback
  }
  observe(): void {
    // no-op for tests
  }
  unobserve(): void {
    // no-op for tests
  }
  disconnect(): void {
    // no-op for tests
  }
}

if (typeof window !== 'undefined' && !('ResizeObserver' in window)) {
  // @ts-expect-error jsdom global mutation for test environment
  window.ResizeObserver = ResizeObserverMock
}

if (typeof window !== 'undefined' && !window.matchMedia) {
  window.matchMedia = (query: string): MediaQueryList => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  })
}
