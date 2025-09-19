import { MoonIcon, SunIcon } from '@heroicons/react/24/outline'
import { useTheme } from '../hooks/useTheme'

const iconClasses = 'h-5 w-5'

export const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="inline-flex items-center gap-2 rounded-full border border-slate-200/70 bg-white/80 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm backdrop-blur-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-white/10 dark:bg-white/10 dark:text-slate-200"
    >
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900/5 text-slate-700 dark:bg-white/10 dark:text-slate-100">
        {isDark ? <MoonIcon className={iconClasses} /> : <SunIcon className={iconClasses} />}
      </span>
      <span>{isDark ? 'Dark mode' : 'Light mode'}</span>
    </button>
  )
}
