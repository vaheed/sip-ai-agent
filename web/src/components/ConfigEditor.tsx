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
    <div className="relative overflow-hidden rounded-3xl border border-white/60 bg-white/80 p-6 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-white/5 sm:p-8">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.12),_transparent_75%)] dark:bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),_transparent_80%)]" />
      <form className="space-y-6" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-600 dark:bg-blue-500/20 dark:text-blue-200">
              <AdjustmentsHorizontalIcon className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">Configuration</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Update SIP and agent parameters with instant environment persistence.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-slate-900/5 px-3 py-1 text-xs text-slate-500 dark:bg-white/5 dark:text-slate-300">
            <CheckCircleIcon className="h-4 w-4" />
            <span>Changes persist to the .env file</span>
          </div>
        </div>

        {successMessage ? (
          <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-100">
            {reloadStatus?.status === 'restarting' ? (
              <ArrowPathIcon className="mt-0.5 h-5 w-5 animate-spin" />
            ) : (
              <CheckCircleIcon className="mt-0.5 h-5 w-5" />
            )}
            <div className="space-y-1">
              <p>{successMessage}</p>
              {reloadDetail ? <p className="text-xs text-emerald-600 dark:text-emerald-200/80">{reloadDetail}</p> : null}
            </div>
          </div>
        ) : null}
        {errorMessage ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50/80 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100">
            {errorMessage}
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {CONFIG_KEYS.map((key) => {
            const value = formValues[key] ?? ''
            const isTextarea = textareaKeys.includes(key)
            return (
              <label key={key} className="flex flex-col gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                <span className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{key}</span>
                {isTextarea ? (
                  <textarea
                    value={value}
                    onChange={(event) => handleChange(key, event.target.value)}
                    rows={6}
                    className="min-h-[160px] rounded-2xl border border-slate-200/80 bg-white/90 px-3 py-2 text-sm text-slate-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:focus:border-blue-400 dark:focus:ring-blue-900/60"
                  />
                ) : (
                  <input
                    type="text"
                    value={value}
                    onChange={(event) => handleChange(key, event.target.value)}
                    className="rounded-2xl border border-slate-200/80 bg-white/90 px-3 py-2 text-sm text-slate-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:focus:border-blue-400 dark:focus:ring-blue-900/60"
                  />
                )}
              </label>
            )
          })}
        </div>

        <div className="flex flex-col gap-4 border-t border-slate-200/70 pt-4 text-sm dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">
          <div className="text-xs text-slate-500 dark:text-slate-400">
            Saving applies immediately to the environment file. Restart containers to propagate changes.
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-400 hover:text-slate-800 dark:border-white/20 dark:text-slate-200 dark:hover:border-white/40 dark:hover:text-white"
            >
              <ArrowPathIcon className={`h-4 w-4 ${saving ? 'animate-spin' : ''}`} />
              Reset
            </button>
            <button
              type="submit"
              disabled={!hasChanges || saving}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
            >
              {saving ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
