import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useAuthStore } from '@/stores/auth'
import { PortalSetPasswordForm } from '@/components/portal/PortalSetPasswordForm'
import { PortalAdvancedPanel } from '@/components/portal/PortalAdvancedPanel'
import { PortalAiConfigManager } from '@/components/portal/PortalAiConfigManager'

export function PortalAccountPage() {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)

  return (
    <div className="space-y-8 max-w-2xl text-gray-900 dark:text-gray-200">
      <Link
        to="/portal/dashboard"
        className="inline-flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-primary-600"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('portal.backDashboard')}
      </Link>

      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
          {t('portal.accountTitle')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {user?.phone || user?.username}
          {user?.email && ` · ${user.email}`}
        </p>
      </div>

      {user?.can_set_password !== false && (
        <section className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            {t('portal.setPasswordTitle')}
          </h2>
          <PortalSetPasswordForm />
        </section>
      )}

      {user?.external_provider && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t('portal.password9235Hint')}
        </p>
      )}

      <PortalAdvancedPanel hint={t('portal.accountAdvancedAiHint')}>
        <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200 -mt-2 mb-2">
          {t('portal.aiConfigManageTitle')}
        </h2>
        <PortalAiConfigManager />
      </PortalAdvancedPanel>
    </div>
  )
}
