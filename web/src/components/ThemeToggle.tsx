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
      className="inline-flex items-center gap-2 rounded-full border border-border-light bg-white/80 px-4 py-2 text-sm font-medium text-gray-700 shadow-sm backdrop-blur transition hover:bg-white dark:border-border-dark dark:bg-gray-800/80 dark:text-gray-200 dark:hover:bg-gray-700"
    >
      {isDark ? <MoonIcon className={iconClasses} /> : <SunIcon className={iconClasses} />}
      <span>{isDark ? 'Dark mode' : 'Light mode'}</span>
    </button>
  )
}
