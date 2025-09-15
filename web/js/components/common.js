/**
 * Common Components and Utilities
 * Shared components and utility functions
 */

// Status Card Component
function StatusCard({ title, status, value, icon, color, loading }) {
    const getStatusColor = (status, color) => {
        if (color === 'green') return 'text-green-600 dark:text-green-400';
        if (color === 'red') return 'text-red-600 dark:text-red-400';
        if (color === 'blue') return 'text-blue-600 dark:text-blue-400';
        if (color === 'yellow') return 'text-yellow-600 dark:text-yellow-400';
        return 'text-gray-600 dark:text-gray-400';
    };

    const getStatusIcon = (status) => {
        if (status === 'online') return '🟢';
        if (status === 'offline') return '🔴';
        return '⚪';
    };

    return (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <div className="flex items-center">
                <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-md flex items-center justify-center ${
                        color === 'green' ? 'bg-green-100 dark:bg-green-900/20' :
                        color === 'red' ? 'bg-red-100 dark:bg-red-900/20' :
                        color === 'blue' ? 'bg-blue-100 dark:bg-blue-900/20' :
                        color === 'yellow' ? 'bg-yellow-100 dark:bg-yellow-900/20' :
                        'bg-gray-100 dark:bg-gray-700'
                    }`}>
                        <span className="text-sm">{icon}</span>
                    </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                    <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                            {title}
                        </dt>
                        <dd className="flex items-baseline">
                            <div className={`text-2xl font-semibold ${getStatusColor(status, color)}`}>
                                {loading ? (
                                    <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-6 w-16 rounded"></div>
                                ) : (
                                    <>
                                        {getStatusIcon(status)} {value}
                                    </>
                                )}
                            </div>
                        </dd>
                    </dl>
                </div>
            </div>
        </div>
    );
}

// Loading Spinner Component
function LoadingSpinner({ size = 'h-8 w-8', text = 'Loading...' }) {
    return (
        <div className="flex items-center justify-center py-12">
            <div className={`loading-spinner rounded-full ${size} border-b-2 border-indigo-600`}></div>
            <span className="ml-2 text-gray-600 dark:text-gray-400">{text}</span>
        </div>
    );
}

// Error Message Component
function ErrorMessage({ error, onRetry }) {
    return (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
            <div className="flex">
                <div className="flex-shrink-0">
                    <span className="text-red-400">⚠️</span>
                </div>
                <div className="ml-3">
                    <p className="text-red-600 dark:text-red-400">{error}</p>
                    {onRetry && (
                        <div className="mt-2">
                            <button
                                onClick={onRetry}
                                className="text-sm bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 text-red-800 dark:text-red-200 px-3 py-1 rounded-md"
                            >
                                Try Again
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// Success Message Component
function SuccessMessage({ message }) {
    return (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4">
            <div className="flex">
                <div className="flex-shrink-0">
                    <span className="text-green-400">✅</span>
                </div>
                <div className="ml-3">
                    <p className="text-green-600 dark:text-green-400">{message}</p>
                </div>
            </div>
        </div>
    );
}

// Empty State Component
function EmptyState({ icon, title, description, action }) {
    return (
        <div className="text-center py-12">
            <div className="text-6xl mb-4">{icon}</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{title}</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">{description}</p>
            {action && action}
        </div>
    );
}

// Utility Functions
const utils = {
    formatDate: (timestamp) => {
        if (!timestamp) return '-';
        return new Date(timestamp * 1000).toLocaleString();
    },
    
    formatDuration: (start, end) => {
        if (!start || !end) return '-';
        const duration = end - start;
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    },
    
    formatCurrency: (amount, decimals = 4) => {
        if (!amount) return '$0.0000';
        return `$${parseFloat(amount).toFixed(decimals)}`;
    },
    
    formatNumber: (number) => {
        if (!number) return '0';
        return number.toLocaleString();
    },
    
    formatPercentage: (value) => {
        if (!value) return '0%';
        return `${Math.round(value * 100)}%`;
    },
    
    getLogLevel: (log) => {
        if (log.toLowerCase().includes('error')) return 'error';
        if (log.toLowerCase().includes('warn')) return 'warning';
        if (log.toLowerCase().includes('info')) return 'info';
        if (log.toLowerCase().includes('debug')) return 'debug';
        return 'info';
    },
    
    getLogColor: (level) => {
        switch (level) {
            case 'error': return 'text-red-600 dark:text-red-400';
            case 'warning': return 'text-yellow-600 dark:text-yellow-400';
            case 'info': return 'text-blue-600 dark:text-blue-400';
            case 'debug': return 'text-gray-600 dark:text-gray-400';
            default: return 'text-gray-800 dark:text-gray-200';
        }
    },
    
    getStatusColor: (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
            case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
            case 'active': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
            default: return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
        }
    }
};
