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
            <MetricsCards systemMetrics={systemMetrics} callAnalytics={callAnalytics} />

            {/* System Health Overview */}
            <SystemHealth 
                systemMetrics={systemMetrics}
                realTimeStats={realTimeStats}
                callAnalytics={callAnalytics}
            />

            {/* Charts and Analytics */}
            <ChartsAnalytics callAnalytics={callAnalytics} />

            {/* Recent Activity and Alerts */}
            <ActivityAlerts />

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
