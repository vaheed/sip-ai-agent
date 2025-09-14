import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText('SIP AI Agent Web UI')).toBeInTheDocument()
  })

  it('displays welcome message', () => {
    render(<App />)
    expect(screen.getByText('Modern React frontend with Tailwind CSS')).toBeInTheDocument()
  })
})
