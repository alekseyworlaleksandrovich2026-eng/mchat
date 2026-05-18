import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft } from 'lucide-react'
import { GithubLink } from '@/components/common/GithubLink'
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher'
import { ChatWindow } from '@/components/chat/ChatWindow'
import { useChat } from '@/hooks/useChat'

export function ChatPage() {
  const { t } = useTranslation()
  const { conversationId } = useParams<{ conversationId: string }>()
  const navigate = useNavigate()
  const chat = useChat(conversationId)

  const handleSend = (content: string, file?: File) => {
    if (conversationId) {
      chat.sendMessage(conversationId, content, file)
    }
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <header className="shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate('/admin/conversations')}
          className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-base font-semibold text-gray-900 dark:text-gray-100 truncate">
            {chat.currentConversation?.title || t('chat.defaultTitle')}
          </h1>
          <p className="text-xs text-gray-500 truncate">
            {chat.currentConversation?.visitor_id || conversationId}
          </p>
        </div>
        <LanguageSwitcher variant="ghost" />
        <GithubLink />
      </header>

      {chat.error && (
        <div className="shrink-0 mx-4 mt-2 px-4 py-2 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">
          {chat.error}
          <button
            onClick={() => chat.setError(null)}
            className="ml-2 underline hover:no-underline"
          >
            {t('common.close')}
          </button>
        </div>
      )}

      <div className="flex-1 min-h-0">
        <ChatWindow
          messages={chat.messages}
          isStreaming={chat.isStreaming}
          streamingContent={chat.streamingContent}
          onSend={handleSend}
          disabled={chat.isStreaming}
          emptyMessage={t('chat.emptyMessage')}
          speechConfigUrl="/api/speech/config"
          speechTranscribeUrl="/api/speech/transcribe"
        />
      </div>
    </div>
  )
}
