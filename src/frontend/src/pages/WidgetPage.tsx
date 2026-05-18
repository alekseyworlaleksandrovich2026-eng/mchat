import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Widget } from '@/components/widget/Widget'
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher'

/** Standalone full-page widget (iframe / direct link). */
export function WidgetPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const agentId =
    searchParams.get('agentId') ||
    searchParams.get('agent_id') ||
    ''

  if (!agentId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="absolute top-4 right-4">
          <LanguageSwitcher />
        </div>
        <div className="max-w-md text-center space-y-3">
          <h1 className="text-lg font-semibold text-gray-900">{t('chat.missingAgentId')}</h1>
          <p className="text-sm text-gray-500">
            {t('chat.missingAgentHint')}
            <br />
            <code className="text-xs bg-gray-200 px-2 py-1 rounded mt-2 inline-block dark:bg-gray-700">
              {t('chat.missingAgentExample')}
            </code>
          </p>
          <a href="/widget/demo" className="text-sm text-primary-600 hover:underline">
            {t('chat.goWidgetDemo')}
          </a>
        </div>
      </div>
    )
  }

  return (
  <>
      <div className="absolute top-3 right-3 z-[10000]">
        <LanguageSwitcher />
      </div>
      <Widget
        variant="page"
        agentId={agentId}
        apiUrl="/api"
        wsUrl="/ws"
        defaultOpen
      />
    </>
  )
}
