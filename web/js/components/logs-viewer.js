/**
 * Logs Viewer Component
 * Displays system logs with filtering and real-time updates
 */

function LogsViewer() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [autoScroll, setAutoScroll] = useState(true);
    const [filter, setFilter] = useState('');
    const [logLevel, setLogLevel] = useState('all');

    const loadLogs = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.get('/logs');
            setLogs(response.data.logs || []);
            setError(null);
        } catch (err) {
            console.error('Failed to load logs:', err);
            setError('Failed to load logs');
        } finally {
            setLoading(false);
        }
    }, []);

    const clearLogs = async () => {
        try {
            // Note: This would require a backend endpoint to clear logs
            setLogs([]);
        } catch (err) {
            console.error('Failed to clear logs:', err);
            setError('Failed to clear logs');
        }
    };

    useEffect(() => {
        loadLogs();
        const interval = setInterval(loadLogs, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, [loadLogs]);

    const filteredLogs = logs.filter(log => {
        const matchesFilter = !filter || log.toLowerCase().includes(filter.toLowerCase());
        const matchesLevel = logLevel === 'all' || log.toLowerCase().includes(logLevel);
        return matchesFilter && matchesLevel;
    });

    const getLogLevel = (log) => {
        if (log.toLowerCase().includes('error')) return 'error';
        if (log.toLowerCase().includes('warn')) return 'warning';
        if (log.toLowerCase().includes('info')) return 'info';
        if (log.toLowerCase().includes('debug')) return 'debug';
        return 'info';
    };

    const getLogColor = (level) => {
        switch (level) {
            case 'error': return 'text-red-600 dark:text-red-400';
            case 'warning': return 'text-yellow-600 dark:text-yellow-400';
            case 'info': return 'text-blue-600 dark:text-blue-400';
            case 'debug': return 'text-gray-600 dark:text-gray-400';
            default: return 'text-gray-800 dark:text-gray-200';
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="loading-spinner rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading logs...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                        System Logs
                    </h2>
                    <div className="flex space-x-2">
                        <button
                            onClick={clearLogs}
                            className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
                        >
                            🗑️ Clear
                        </button>
                        <button
                            onClick={loadLogs}
                            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                        >
                            🔄 Refresh
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                        <p className="text-red-600 dark:text-red-400">{error}</p>
                    </div>
                )}

                {/* Filters */}
                <div className="mb-4 flex space-x-4">
                    <div className="flex-1">
                        <input
                            type="text"
                            placeholder="Filter logs..."
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                        />
                    </div>
                    <select
                        value={logLevel}
                        onChange={(e) => setLogLevel(e.target.value)}
                        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                    >
                        <option value="all">All Levels</option>
                        <option value="error">Error</option>
                        <option value="warning">Warning</option>
                        <option value="info">Info</option>
                        <option value="debug">Debug</option>
                    </select>
                    <label className="flex items-center">
                        <input
                            type="checkbox"
                            checked={autoScroll}
                            onChange={(e) => setAutoScroll(e.target.checked)}
                            className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                        />
                        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">Auto-scroll</span>
                    </label>
                </div>

                {/* Logs Display */}
                <div className="bg-gray-900 text-green-400 font-mono text-sm rounded-lg p-4 h-96 overflow-y-auto">
                    {filteredLogs.length === 0 ? (
                        <div className="text-center py-8">
                            <p className="text-gray-500">No logs available</p>
                        </div>
                    ) : (
                        filteredLogs.map((log, index) => {
                            const level = getLogLevel(log);
                            return (
                                <div key={index} className={`mb-1 ${getLogColor(level)}`}>
                                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
                                    <span className="ml-2">{log}</span>
                                </div>
                            );
                        })
                    )}
                </div>

                <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Showing {filteredLogs.length} of {logs.length} logs
                </div>
            </div>
        </div>
    );
}
