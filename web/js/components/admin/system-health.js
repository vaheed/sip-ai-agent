/**
 * System Health Component
 * Displays system health overview with SIP status, resources, and API usage
 */

function SystemHealth({ systemMetrics, realTimeStats, callAnalytics }) {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* SIP Status */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    📡 SIP Status
                </h3>
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Registration</span>
                        <div className="flex items-center">
                            <div className={`w-3 h-3 rounded-full mr-2 ${
                                systemMetrics?.sip_registered ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                            }`}></div>
                            <span className={`text-sm font-medium ${
                                systemMetrics?.sip_registered ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                            }`}>
                                {systemMetrics?.sip_registered ? 'Connected' : 'Disconnected'}
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Active Calls</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {systemMetrics?.active_calls?.length || 0}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Uptime</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {systemMetrics?.uptime_seconds ? 
                                `${Math.floor(systemMetrics.uptime_seconds / 3600)}h ${Math.floor((systemMetrics.uptime_seconds % 3600) / 60)}m` : 
                                '0h 0m'
                            }
                        </span>
                    </div>
                </div>
            </div>

            {/* System Resources */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    💻 System Resources
                </h3>
                <div className="space-y-4">
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600 dark:text-gray-400">CPU Usage</span>
                            <span className="text-gray-900 dark:text-white">{realTimeStats?.cpu?.usage_percent?.toFixed(1) || 0}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div 
                                className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                                style={{ width: `${realTimeStats?.cpu?.usage_percent || 0}%` }}
                            ></div>
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600 dark:text-gray-400">Memory Usage</span>
                            <span className="text-gray-900 dark:text-white">{realTimeStats?.memory?.usage_percent?.toFixed(1) || 0}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div 
                                className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                                style={{ width: `${realTimeStats?.memory?.usage_percent || 0}%` }}
                            ></div>
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600 dark:text-gray-400">Disk Usage</span>
                            <span className="text-gray-900 dark:text-white">{realTimeStats?.disk?.usage_percent?.toFixed(1) || 0}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div 
                                className="bg-orange-500 h-2 rounded-full transition-all duration-300" 
                                style={{ width: `${realTimeStats?.disk?.usage_percent || 0}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            </div>

            {/* API Usage */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    🎯 API Usage
                </h3>
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Total Tokens</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {callAnalytics?.total_tokens?.toLocaleString() || '0'}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Avg per Call</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {callAnalytics?.average_tokens_per_call ? Math.round(callAnalytics.average_tokens_per_call) : '0'}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Cost per Token</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                            ${callAnalytics?.cost_per_token ? parseFloat(callAnalytics.cost_per_token).toFixed(6) : '0.000000'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
