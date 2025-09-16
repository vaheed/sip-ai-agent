/**
 * Charts and Analytics Component
 * Displays call volume trends and success distribution charts
 */

function ChartsAnalytics({ callAnalytics }) {
    return (
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
    );
}
