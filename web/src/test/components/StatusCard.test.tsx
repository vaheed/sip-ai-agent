import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

// Mock component for testing
const StatusCard = ({ title, status, value, icon, color = 'blue', loading = false }) => {
  // Suppress unused parameter warning for color
  void color;
  return (
    <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center`}>
              {loading ? '⏳' : icon}
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {loading ? '...' : value}
                </div>
                {status && !loading && (
                  <div className="ml-2 flex items-baseline text-sm font-semibold">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                      {status}
                    </span>
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}

describe('StatusCard', () => {
  it('renders with basic props', () => {
    render(
      <StatusCard
        title="Test Status"
        value="100"
        icon="📊"
        color="blue"
      />
    )

    expect(screen.getByText('Test Status')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
    expect(screen.getByText('📊')).toBeInTheDocument()
  })

  it('renders with status indicator', () => {
    render(
      <StatusCard
        title="SIP Registration"
        status="online"
        value="Registered"
        icon="📞"
        color="green"
      />
    )

    expect(screen.getByText('SIP Registration')).toBeInTheDocument()
    expect(screen.getByText('Registered')).toBeInTheDocument()
    expect(screen.getByText('online')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <StatusCard
        title="Loading Test"
        value="100"
        icon="📊"
        loading={true}
      />
    )

    expect(screen.getByText('Loading Test')).toBeInTheDocument()
    expect(screen.getByText('...')).toBeInTheDocument()
    expect(screen.getByText('⏳')).toBeInTheDocument()
  })
})