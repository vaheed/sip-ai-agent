/**
 * Configuration Component
 * Manages SIP and OpenAI configuration settings
 */

function Configuration() {
    const [config, setConfig] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const loadConfig = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.get('/config');
            setConfig(response.data);
            setError(null);
        } catch (err) {
            console.error('Failed to load configuration:', err);
            setError('Failed to load configuration');
        } finally {
            setLoading(false);
        }
    }, []);

    const saveConfig = async () => {
        try {
            setSaving(true);
            setError(null);
            setSuccess(null);
            
            await api.post('/config', config);
            await api.post('/config/reload');
            
            setSuccess('Configuration saved and reloaded successfully');
        } catch (err) {
            console.error('Failed to save configuration:', err);
            setError('Failed to save configuration');
        } finally {
            setSaving(false);
        }
    };

    const handleConfigChange = (section, key, value) => {
        setConfig(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [key]: value
            }
        }));
    };

    useEffect(() => {
        loadConfig();
    }, [loadConfig]);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="loading-spinner rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading configuration...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                        Configuration
                    </h2>
                    <button
                        onClick={saveConfig}
                        disabled={saving}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        {saving ? '💾 Saving...' : '💾 Save & Reload'}
                    </button>
                </div>

                {error && (
                    <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                        <p className="text-red-600 dark:text-red-400">{error}</p>
                    </div>
                )}

                {success && (
                    <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                        <p className="text-green-600 dark:text-green-400">{success}</p>
                    </div>
                )}

                {/* SIP Configuration */}
                <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        📞 SIP Configuration
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                SIP Domain
                            </label>
                            <input
                                type="text"
                                value={config.sip?.domain || ''}
                                onChange={(e) => handleConfigChange('sip', 'domain', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                SIP Username
                            </label>
                            <input
                                type="text"
                                value={config.sip?.username || ''}
                                onChange={(e) => handleConfigChange('sip', 'username', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                SIP Password
                            </label>
                            <input
                                type="password"
                                value={config.sip?.password || ''}
                                onChange={(e) => handleConfigChange('sip', 'password', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Audio Sample Rate
                            </label>
                            <select
                                value={config.audio?.sample_rate || 16000}
                                onChange={(e) => handleConfigChange('audio', 'sample_rate', parseInt(e.target.value))}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                            >
                                <option value={8000}>8000 Hz</option>
                                <option value={16000}>16000 Hz</option>
                                <option value={44100}>44100 Hz</option>
                                <option value={48000}>48000 Hz</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* OpenAI Configuration */}
                <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        🤖 OpenAI Configuration
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                API Mode
                            </label>
                            <select
                                value={config.openai?.mode || 'realtime'}
                                onChange={(e) => handleConfigChange('openai', 'mode', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                            >
                                <option value="legacy">Legacy API</option>
                                <option value="realtime">Realtime API</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Model
                            </label>
                            <input
                                type="text"
                                value={config.openai?.model || ''}
                                onChange={(e) => handleConfigChange('openai', 'model', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                                placeholder="gpt-4o-mini"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Voice
                            </label>
                            <select
                                value={config.openai?.voice || 'alloy'}
                                onChange={(e) => handleConfigChange('openai', 'voice', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                            >
                                <option value="alloy">Alloy</option>
                                <option value="echo">Echo</option>
                                <option value="fable">Fable</option>
                                <option value="onyx">Onyx</option>
                                <option value="nova">Nova</option>
                                <option value="shimmer">Shimmer</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Max Tokens
                            </label>
                            <input
                                type="number"
                                value={config.openai?.max_tokens || 4096}
                                onChange={(e) => handleConfigChange('openai', 'max_tokens', parseInt(e.target.value))}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                                min="1"
                                max="32768"
                            />
                        </div>
                    </div>
                </div>

                {/* System Configuration */}
                <div className="mb-8">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        ⚙️ System Configuration
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Log Level
                            </label>
                            <select
                                value={config.system?.log_level || 'INFO'}
                                onChange={(e) => handleConfigChange('system', 'log_level', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                            >
                                <option value="DEBUG">DEBUG</option>
                                <option value="INFO">INFO</option>
                                <option value="WARNING">WARNING</option>
                                <option value="ERROR">ERROR</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Metrics Enabled
                            </label>
                            <select
                                value={config.system?.metrics_enabled ? 'true' : 'false'}
                                onChange={(e) => handleConfigChange('system', 'metrics_enabled', e.target.value === 'true')}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                            >
                                <option value="true">Enabled</option>
                                <option value="false">Disabled</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-4">
                    <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                        <strong>Note:</strong> After saving configuration changes, the system will automatically reload the configuration. 
                        Some changes may require a complete restart to take effect.
                    </p>
                </div>
            </div>
        </div>
    );
}
