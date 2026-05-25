import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { toast } from '@/components/ui/Toast'

export function PortalSetPasswordForm() {
  const { t } = useTranslation()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [useCurrent, setUseCurrent] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      toast(t('users.passwordMismatch'), { type: 'error' })
      return
    }
    setSaving(true)
    try {
      await api.post('/auth/set-password', {
        new_password: newPassword,
        current_password: useCurrent ? currentPassword : undefined,
      })
      toast(t('users.passwordChanged'), { type: 'success' })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t('users.passwordChangeFailed')
      toast(message, { type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t('portal.setPasswordHint')}
      </p>
      <label className="flex items-center gap-2 text-sm cursor-pointer text-gray-700 dark:text-gray-300">
        <input
          type="checkbox"
          checked={useCurrent}
          onChange={(e) => setUseCurrent(e.target.checked)}
          className="rounded border-gray-300"
        />
        {t('portal.haveOldPassword')}
      </label>
      {useCurrent && (
        <Input
          label={t('users.currentPassword')}
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          autoComplete="current-password"
        />
      )}
      <Input
        label={t('users.newPassword')}
        type="password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        required
        minLength={6}
        autoComplete="new-password"
      />
      <Input
        label={t('users.confirmPassword')}
        type="password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        required
        minLength={6}
        autoComplete="new-password"
      />
      <Button type="submit" isLoading={saving}>
        {t('portal.savePassword')}
      </Button>
    </form>
  )
}
