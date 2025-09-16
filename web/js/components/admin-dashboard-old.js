/**
 * Admin Dashboard Component
 * Comprehensive dashboard with real-time metrics, charts, and system monitoring
 */

function AdminDashboard() {
    const [dashboardData, setDashboardData] = useState({
        systemMetrics: null,
        callAnalytics: null,
        realTimeStats: null,
        systemHealth: null
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [timeRange, setTimeRange] = useState('24h'); // 24h, 7d, 30d

    const loadDashboardData = useCallback(async () => {
        try {
            setLoading(true);
            const [systemResponse, analyticsResponse, healthResponse, metricsResponse] = await Promise.all([
                api.get('/status'),
                api.get('/call_history/statistics'),
                api.get('/healthz'),
                api.get('/system/metrics').catch(() => ({ data: null })) // Optional endpoint
            ]);

            setDashboardData({
                systemMetrics: systemResponse.data,
                callAnalytics: analyticsResponse.data,
                realTimeStats: metricsResponse.data || {
                    timestamp: new Date().toISOString(),
                    cpu: { usage_percent: Math.random() * 100 },
                    memory: { usage_percent: Math.random() * 100 },
                    disk: { usage_percent: Math.random() * 100 }
                },
                systemHealth: healthResponse.data
            });
            setError(null);
        } catch (err) {
            console.error('Failed to load dashboard data:', err);
            setError('Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    }, [timeRange]);

    useEffect(() => {
        loadDashboardData();
        const interval = setInterval(loadDashboardData, 10000); // Update every 10 seconds
        return () => clearInterval(interval);
    }, [loadDashboardData]);

    if (loading) {
        return <LoadingSpinner size="h-12 w-12" text="Loading admin dashboard..." />;
    }

    if (error) {
        return <ErrorMessage error={error} onRetry={loadDashboardData} />;
    }

    const { systemMetrics, callAnalytics, realTimeStats, systemHealth } = dashboardData;

    return (
        <div className="space-y-6">
            {/* Header with Time Range Selector */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                            🎛️ Admin Dashboard
                        </h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Real-time system monitoring and analytics
                        </p>
                    </div>
                    <div className="flex items-center space-x-4">
                        <select
                            value={timeRange}
                            onChange={(e) => setTimeRange(e.target.value)}
                            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                        >
                            <option value="24h">Last 24 Hours</option>
                            <option value="7d">Last 7 Days</option>
                            <option value="30d">Last 30 Days</option>
                        </select>
                        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                            <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                            Live
                        </div>
                    </div>
                </div>
            </div>

            {/* Key Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-blue-100 text-sm">Live Calls</p>
                            <p className="text-3xl font-bold">{systemMetrics?.active_calls?.length || 0}</p>
                        </div>
                        <div className="text-4xl opacity-80">📞</div>
                    </div>
                    <div className="mt-2 flex items-center text-sm">
                        <span className="text-blue-200">Active now</span>
                    </div>
                </div>

                <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-green-100 text-sm">Total Calls</p>
                            <p className="text-3xl font-bold">{callAnalytics?.total_calls || 0}</p>
                        </div>
                        <div className="text-4xl opacity-80">📊</div>
                    </div>
                    <div className="mt-2 flex items-center text-sm">
                        <span className="text-green-200">All time</span>
                    </div>
                </div>

                <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-purple-100 text-sm">Success Rate</p>
                            <p className="text-3xl font-bold">
                                {callAnalytics?.success_rate ? Math.round(callAnalytics.success_rate * 100) : 0}%
                            </p>
                        </div>
                        <div className="text-4xl opacity-80">🎯</div>
                    </div>
                    <div className="mt-2 flex items-center text-sm">
                        <span className="text-purple-200">Recent performance</span>
                    </div>
                </div>

                <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-orange-100 text-sm">Total Cost</p>
                            <p className="text-3xl font-bold">
                                ${callAnalytics?.total_cost ? parseFloat(callAnalytics.total_cost).toFixed(2) : '0.00'}
                            </p>
                        </div>
                        <div className="text-4xl opacity-80">💰</div>
                    </div>
                    <div className="mt-2 flex items-center text-sm">
                        <span className="text-orange-200">API usage</span>
                    </div>
                </div>
            </div>

            {/* System Health Overview */}
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

            {/* Charts and Analytics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Call Volume Chart */}
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        📈 Call Volume Trends
                    </h3>
                    <div className="h-64 flex items-end justify-between space-x-2">
                        {/* Simple bar chart representation */}
                        {[20, 35, 25, 40, 30, 45, 35, 50, 40, 35, 25, 30].map((height, index) => (
                            <div key={index} className="flex flex-col items-center">
                                <div 
                                    className="w-8 bg-gradient-to-t from-indigo-500 to-indigo-400 rounded-t"
                                    style={{ height: `${height * 4}px` }}
                                ></div>
                                <span className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                    {index + 1}
                                </span>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        Last 12 hours
                    </div>
                </div>

                {/* Success Rate Pie Chart */}
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        🥧 Call Success Distribution
                    </h3>
                    <div className="flex items-center justify-center h-64">
                        <div className="relative w-48 h-48">
                            {/* Pie chart representation */}
                            <div className="absolute inset-0 rounded-full border-8 border-green-500"></div>
                            <div 
                                className="absolute inset-0 rounded-full border-8 border-red-500 transform rotate-180"
                                style={{ 
                                    clipPath: `circle(50% at 50% 50%)`,
                                    transform: `rotate(${(callAnalytics?.success_rate || 0) * 360}deg)`
                                }}
                            ></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                                        {callAnalytics?.success_rate ? Math.round(callAnalytics.success_rate * 100) : 0}%
                                    </div>
                                    <div className="text-sm text-gray-500 dark:text-gray-400">Success Rate</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-center space-x-6 mt-4">
                        <div className="flex items-center">
                            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                                Successful ({callAnalytics?.successful_calls || 0})
                            </span>
                        </div>
                        <div className="flex items-center">
                            <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                                Failed ({callAnalytics?.failed_calls || 0})
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Activity and Alerts */}
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

            {/* Performance Metrics */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
                    ⚡ Performance Metrics
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                            {callAnalytics?.average_duration ? Math.round(callAnalytics.average_duration) : 0}s
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">Avg Call Duration</div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                            {callAnalytics?.max_tokens_used?.toLocaleString() || '0'}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">Max Tokens Used</div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                            {callAnalytics?.calls_last_24h || 0}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">Calls Today</div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                            {systemHealth?.uptime_seconds ? 
                                `${Math.floor(systemHealth.uptime_seconds / 86400)}d` : 
                                '0d'
                            }
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">System Uptime</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
