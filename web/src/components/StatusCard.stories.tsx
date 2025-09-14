import type { Meta, StoryObj } from '@storybook/react'

const StatusCard = ({ title, status, value, icon, color = 'blue', loading = false }) => {
  return (
    <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              color === 'green' ? 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900' :
              color === 'red' ? 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900' :
              color === 'blue' ? 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900' :
              'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900'
            }`}>
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
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      status === 'online' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                      status === 'offline' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                    }`}>
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

const meta: Meta<typeof StatusCard> = {
  title: 'Components/StatusCard',
  component: StatusCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    status: { control: 'text' },
    value: { control: 'text' },
    icon: { control: 'text' },
    color: { control: 'select', options: ['blue', 'green', 'red', 'yellow'] },
    loading: { control: 'boolean' },
  },
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    title: 'Test Status',
    value: '100',
    icon: '📊',
    color: 'blue',
  },
}

export const WithStatus: Story = {
  args: {
    title: 'SIP Registration',
    status: 'online',
    value: 'Registered',
    icon: '📞',
    color: 'green',
  },
}

export const Loading: Story = {
  args: {
    title: 'Loading Status',
    value: '100',
    icon: '📊',
    color: 'blue',
    loading: true,
  },
}

export const Offline: Story = {
  args: {
    title: 'SIP Registration',
    status: 'offline',
    value: 'Not Registered',
    icon: '📞',
    color: 'red',
  },
}
