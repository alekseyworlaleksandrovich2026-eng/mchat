import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { MessageCircle } from 'lucide-react'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher'

export function RegisterPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { signup, isLoading, error, clearError } = useAuthStore()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setLocalError(null)
    if (password !== confirmPassword) {
      setLocalError(t('auth.passwordMismatch'))
      return
    }
    try {
      await signup(username, password, email || undefined, displayName || undefined)
      navigate('/portal/dashboard', { replace: true })
    } catch { /* store handles error */ }
  }

  const displayError = localError || error

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 p-4">
      <div className="absolute top-4 right-4"><LanguageSwitcher /></div>
      <div className="absolute top-4 left-4">
        <Link to="/" className="text-sm text-gray-500 hover:text-primary-600 dark:text-gray-400">
          ← {t('common.home')}
        </Link>
      </div>
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-600 mb-4">
            <MessageCircle className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">MChat</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t('auth.registerTagline')}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">{t('auth.registerTitle')}</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            {displayError && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">{displayError}</div>
            )}
            <Input label={t('auth.username')} type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder={t('auth.usernamePlaceholder')} autoComplete="username" required />
            <Input label={t('auth.email')} type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('auth.emailPlaceholder')} autoComplete="email" />
            <Input label={t('auth.displayNamePlaceholder')} type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder={t('auth.displayNamePlaceholder')} />
            <Input label={t('auth.password')} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t('auth.passwordPlaceholder')} autoComplete="new-password" required />
            <Input label={t('auth.confirmPassword')} type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder={t('auth.confirmPasswordPlaceholder')} autoComplete="new-password" required />
            <Button type="submit" className="w-full" size="lg" isLoading={isLoading}>{t('auth.signup')}</Button>
          </form>
          <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
            {t('auth.haveAccount')}{' '}
            <Link to="/admin/login" className="text-primary-600 hover:text-primary-700 dark:text-primary-400 font-medium">{t('auth.signIn')}</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
