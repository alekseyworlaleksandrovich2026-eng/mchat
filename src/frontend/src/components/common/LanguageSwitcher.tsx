import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { setAppLanguage, type AppLanguage } from '@/i18n'

interface LanguageSwitcherProps {
  className?: string
  variant?: 'pill' | 'ghost'
}

export function LanguageSwitcher({
  className,
  variant = 'pill',
}: LanguageSwitcherProps) {
  const { i18n, t } = useTranslation()
  const current = (i18n.language?.startsWith('zh') ? 'zh' : 'en') as AppLanguage

  const setLang = (lang: AppLanguage) => {
    if (lang !== current) setAppLanguage(lang)
  }

  const base =
    variant === 'pill'
      ? 'inline-flex rounded-full border border-gray-200 dark:border-gray-600 bg-gray-100/80 dark:bg-gray-800/80 p-0.5 text-xs font-medium'
      : 'inline-flex gap-1 text-sm'

  return (
    <div
      className={cn(base, className)}
      role="group"
      aria-label={t('common.language')}
    >
      {(['zh', 'en'] as const).map((lang) => (
        <button
          key={lang}
          type="button"
          onClick={() => setLang(lang)}
          className={cn(
            'px-2.5 py-1 rounded-full transition-colors',
            variant === 'pill' &&
              (current === lang
                ? 'bg-white dark:bg-gray-700 text-primary-700 dark:text-primary-300 shadow-sm'
                : 'text-gray-500 hover:text-gray-800 dark:text-gray-400'),
            variant === 'ghost' &&
              (current === lang
                ? 'text-primary-600 font-semibold'
                : 'text-gray-500 hover:text-gray-800'),
          )}
        >
          {t(`common.${lang}`)}
        </button>
      ))}
    </div>
  )
}
