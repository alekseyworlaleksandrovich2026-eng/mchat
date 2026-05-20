import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { MessageSquare, ExternalLink } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { ConversationList, type ConversationStats } from '@/components/admin/ConversationList'
import { Conversation } from '@/stores/chat'
import { Button } from '@/components/ui/Button'

export function ConversationsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null)
  const [stats, setStats] = useState<ConversationStats>({
    total: 0,
    active: 0,
    closed: 0,
  })

  const handleSelect = (conv: Conversation) => {
    setSelectedConv(conv)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t('conversations.pageTitle')}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t('conversations.pageSubtitle')}
          </p>
        </div>
        {selectedConv && (
          <Button
            variant="outline"
            leftIcon={<ExternalLink className="w-4 h-4" />}
            onClick={() => navigate(`/chat/${selectedConv.id}`)}
          >
            {t('conversations.viewDetail')}
          </Button>
        )}
      </div>

      <ConversationList onSelect={handleSelect} onStatsChange={setStats} />

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 text-gray-400 mb-1">
            <MessageSquare className="w-4 h-4" />
            <span className="text-xs">{t('conversations.statActive')}</span>
          </div>
          <p className="text-lg font-semibold text-green-600">{stats.active}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 text-gray-400 mb-1">
            <MessageSquare className="w-4 h-4" />
            <span className="text-xs">{t('conversations.statClosed')}</span>
          </div>
          <p className="text-lg font-semibold text-yellow-600">{stats.closed}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 text-gray-400 mb-1">
            <MessageSquare className="w-4 h-4" />
            <span className="text-xs">{t('conversations.statTotal')}</span>
          </div>
          <p className="text-lg font-semibold text-gray-600">{stats.total}</p>
        </div>
      </div>
    </div>
  )
}
