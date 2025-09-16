/**
 * Activity and Alerts Component
 * Displays recent activity and system alerts
 */

function ActivityAlerts() {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Activity */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    🕒 Recent Activity
                </h3>
                <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <div className="flex-1">
                            <p className="text-sm text-gray-900 dark:text-white">System started successfully</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">2 minutes ago</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <div className="flex-1">
                            <p className="text-sm text-gray-900 dark:text-white">New call initiated</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">5 minutes ago</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                        <div className="flex-1">
                            <p className="text-sm text-gray-900 dark:text-white">High token usage detected</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">10 minutes ago</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <div className="flex-1">
                            <p className="text-sm text-gray-900 dark:text-white">Call completed successfully</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">15 minutes ago</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* System Alerts */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    🚨 System Alerts
                </h3>
                <div className="space-y-3">
                    <div className="flex items-center space-x-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">High CPU Usage</p>
                            <p className="text-xs text-yellow-600 dark:text-yellow-400">CPU usage is above 80%</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-blue-800 dark:text-blue-200">System Update Available</p>
                            <p className="text-xs text-blue-600 dark:text-blue-400">Version 2.1.0 is ready</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-green-800 dark:text-green-200">All Systems Operational</p>
                            <p className="text-xs text-green-600 dark:text-green-400">No critical issues detected</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
