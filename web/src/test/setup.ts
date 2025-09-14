import '@testing-library/jest-dom'

// Mock WebSocket
global.WebSocket = class WebSocket {
  constructor() {
    // Mock implementation
  }
  close() {}
  send() {}
  addEventListener() {}
  removeEventListener() {}
} as any

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as any

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
} as any