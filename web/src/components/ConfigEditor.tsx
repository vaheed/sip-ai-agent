import { type FormEvent, useEffect, useMemo, useState } from 'react'
import { AdjustmentsHorizontalIcon, ArrowPathIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

import { CONFIG_KEYS, type ConfigKey } from '../constants'
import type { ConfigMap, ConfigUpdateResponse, ReloadStatus } from '../types'

interface ConfigEditorProps {
  config: ConfigMap
  onSave: (values: ConfigMap) => Promise<ConfigUpdateResponse>
}

const textareaKeys: ConfigKey[] = ['SYSTEM_PROMPT']

export const ConfigEditor = ({ config, onSave }: ConfigEditorProps) => {
  const [formValues, setFormValues] = useState<ConfigMap>({})
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [reloadStatus, setReloadStatus] = useState<ReloadStatus | null>(null)

  useEffect(() => {
    setFormValues(() => {
      const next: ConfigMap = {}
      for (const key of CONFIG_KEYS) {
        next[key] = config?.[key] ?? ''
      }
      return next
    })
  }, [config])

  const handleChange = (key: ConfigKey, value: string) => {
    setFormValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleReset = () => {
    setFormValues(() => {
      const next: ConfigMap = {}
      for (const key of CONFIG_KEYS) {
        next[key] = config?.[key] ?? ''
      }
      return next
    })
    setErrorMessage(null)
    setSuccessMessage(null)
    setReloadStatus(null)
  }

  const hasChanges = useMemo(
    () => CONFIG_KEYS.some((key) => (config?.[key] ?? '') !== (formValues?.[key] ?? '')),
    [config, formValues],
  )

  const reloadDetail = useMemo(() => {
    if (!reloadStatus) {
      return null
    }
    if (reloadStatus.status === 'waiting_for_calls') {
      const count = reloadStatus.active_calls
      const callText = count === 1 ? 'the active call ends' : `${count} active calls end`
      return `The service will restart automatically after ${callText}.`
    }
    if (reloadStatus.status === 'restarting') {
      return 'The service is restarting now. The dashboard may briefly disconnect.'
    }
    return null
  }, [reloadStatus])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!hasChanges || saving) {
      return
    }

    setSaving(true)
    setErrorMessage(null)
    setSuccessMessage(null)
    setReloadStatus(null)
    try {
      const response = await onSave(formValues)
      setReloadStatus(response.reload ?? null)
      if (response.reload?.status === 'error') {
        setErrorMessage(response.reload?.message ?? 'Automatic restart failed. Please restart the service manually.')
        setSuccessMessage(null)
      } else {
        const message = response.reload?.message ?? 'Configuration saved.'
        setSuccessMessage(message)
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to save configuration')
      setReloadStatus(null)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="rounded-2xl border border-border-light bg-white/80 p-6 shadow-sm backdrop-blur dark:border-border-dark dark:bg-gray-900/70">
      <form className="space-y-6" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300">
              <AdjustmentsHorizontalIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">Configuration</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Update SIP and agent parameters. Restart required after saving.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <CheckCircleIcon className="h-5 w-5" />
            <span>Changes persist to the .env file</span>
          </div>
        </div>

        {successMessage ? (
          <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50/70 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200">
            {reloadStatus?.status === 'restarting' ? (
              <ArrowPathIcon className="mt-0.5 h-5 w-5 animate-spin" />
            ) : (
              <CheckCircleIcon className="mt-0.5 h-5 w-5" />
            )}
            <div className="space-y-1">
              <p>{successMessage}</p>
              {reloadDetail ? (
                <p className="text-xs text-emerald-700/80 dark:text-emerald-200/80">{reloadDetail}</p>
              ) : null}
            </div>
          </div>
        ) : null}
        {errorMessage ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50/70 px-4 py-3 text-sm text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200">
            {errorMessage}
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2">
          {CONFIG_KEYS.map((key) => {
            const value = formValues[key] ?? ''
            const isTextarea = textareaKeys.includes(key)
            return (
              <label key={key} className="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                <span className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">{key}</span>
                {isTextarea ? (
                  <textarea
                    value={value}
                    onChange={(event) => handleChange(key, event.target.value)}
                    rows={5}
                    className="rounded-xl border border-gray-300 bg-white/80 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-gray-700 dark:bg-gray-900/70 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-900/60"
                  />
                ) : (
                  <input
                    type="text"
                    value={value}
                    onChange={(event) => handleChange(key, event.target.value)}
                    className="rounded-xl border border-gray-300 bg-white/80 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-gray-700 dark:bg-gray-900/70 dark:text-gray-100 dark:focus:border-blue-400 dark:focus:ring-blue-900/60"
                  />
                )}
              </label>
            )
          })}
        </div>

        <div className="flex flex-col gap-3 border-t border-gray-100 pt-4 text-sm dark:border-gray-800 md:flex-row md:items-center md:justify-between">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Saving applies immediately to the environment file. Restart containers to propagate changes.
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center gap-2 rounded-full border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 transition hover:border-gray-400 hover:text-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:border-gray-600 dark:hover:text-gray-100"
            >
              <ArrowPathIcon className={`h-4 w-4 ${saving ? 'animate-spin' : ''}`} />
              Reset
            </button>
            <button
              type="submit"
              disabled={!hasChanges || saving}
              className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
            >
              {saving ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
