/**
 * Metrics Cards Component
 * Displays key metrics in gradient cards
 */

function MetricsCards({ systemMetrics, callAnalytics }) {
    return (
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
    );
}
