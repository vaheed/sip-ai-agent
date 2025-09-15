/**
 * Statistics Dashboard Component
 * Displays call metrics and analytics
 */

function StatisticsDashboard() {
    const [statistics, setStatistics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadStatistics = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.get('/call_history/statistics');
            setStatistics(response.data);
            setError(null);
        } catch (err) {
            console.error('Failed to load statistics:', err);
            setError('Failed to load statistics');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadStatistics();
    }, [loadStatistics]);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="loading-spinner rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading statistics...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
                <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                                <span className="text-white text-sm font-bold">📞</span>
                            </div>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                            <dl>
                                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                                    Total Calls
                                </dt>
                                <dd className="text-lg font-medium text-gray-900 dark:text-white">
                                    {statistics?.total_calls || 0}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                                <span className="text-white text-sm font-bold">✅</span>
                            </div>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                            <dl>
                                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                                    Successful Calls
                                </dt>
                                <dd className="text-lg font-medium text-gray-900 dark:text-white">
                                    {statistics?.successful_calls || 0}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-red-500 rounded-md flex items-center justify-center">
                                <span className="text-white text-sm font-bold">❌</span>
                            </div>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                            <dl>
                                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                                    Failed Calls
                                </dt>
                                <dd className="text-lg font-medium text-gray-900 dark:text-white">
                                    {statistics?.failed_calls || 0}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                                <span className="text-white text-sm font-bold">💰</span>
                            </div>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                            <dl>
                                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                                    Total Cost
                                </dt>
                                <dd className="text-lg font-medium text-gray-900 dark:text-white">
                                    ${statistics?.total_cost ? parseFloat(statistics.total_cost).toFixed(4) : '0.0000'}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            {/* Detailed Statistics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Call Duration Statistics */}
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        📊 Call Duration Statistics
                    </h3>
                    <div className="space-y-4">
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Average Duration</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {statistics?.average_duration ? `${Math.round(statistics.average_duration)}s` : '0s'}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Longest Call</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {statistics?.longest_call ? `${Math.round(statistics.longest_call)}s` : '0s'}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Shortest Call</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {statistics?.shortest_call ? `${Math.round(statistics.shortest_call)}s` : '0s'}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Total Duration</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {statistics?.total_duration ? `${Math.round(statistics.total_duration / 60)}m` : '0m'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Token Usage Statistics */}
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        🎯 Token Usage Statistics
                    </h3>
                    <div className="space-y-4">
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Total Tokens</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {statistics?.total_tokens?.toLocaleString() || '0'}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Average per Call</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {statistics?.average_tokens_per_call ? Math.round(statistics.average_tokens_per_call) : '0'}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Max Tokens</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {statistics?.max_tokens_used?.toLocaleString() || '0'}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500 dark:text-gray-400">Cost per Token</span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                                ${statistics?.cost_per_token ? parseFloat(statistics.cost_per_token).toFixed(6) : '0.000000'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Success Rate Chart */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    📈 Success Rate Analysis
                </h3>
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500 dark:text-gray-400">Success Rate</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {statistics?.success_rate ? `${Math.round(statistics.success_rate * 100)}%` : '0%'}
                        </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                            className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                            style={{ width: `${statistics?.success_rate ? statistics.success_rate * 100 : 0}%` }}
                        ></div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-4">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                                {statistics?.successful_calls || 0}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">Successful</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                                {statistics?.failed_calls || 0}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">Failed</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    🕒 Recent Activity Summary
                </h3>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                    <p>Last 24 hours: {statistics?.calls_last_24h || 0} calls</p>
                    <p>Last 7 days: {statistics?.calls_last_7d || 0} calls</p>
                    <p>Last 30 days: {statistics?.calls_last_30d || 0} calls</p>
                </div>
            </div>
        </div>
    );
}
