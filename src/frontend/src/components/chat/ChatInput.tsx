import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Send, Paperclip, X, Mic, Square } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useSpeechInput } from '@/hooks/useSpeechInput'

interface ChatInputProps {
  onSend: (content: string, file?: File) => void
  disabled?: boolean
  placeholder?: string
  compact?: boolean
  speechTranscribeUrl?: string
  speechConfigUrl?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder,
  compact = false,
  speechTranscribeUrl,
  speechConfigUrl,
}: ChatInputProps) {
  const { t, i18n } = useTranslation()
  const [content, setContent] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [speechError, setSpeechError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  /** 开始录音前的输入框内容，避免预览与最终写入叠加重复 */
  const speechBaseRef = useRef('')
  const wasListeningRef = useRef(false)

  const speechMessages = useMemo(
    () => ({
      browserUnsupported: t('speech.browserUnsupported'),
      recognitionFailed: t('speech.recognitionFailed'),
      recordingTooShort: t('speech.recordingTooShort'),
      transcribeFailed: t('speech.transcribeFailed'),
      noSpeechDetected: t('speech.noSpeechDetected'),
      speechFailed: t('speech.speechFailed'),
      micDenied: t('speech.micDenied'),
      unavailable: t('speech.unavailable'),
    }),
    [t, i18n.language],
  )

  const appendTranscript = useCallback((text: string, interim?: boolean) => {
    if (!text || interim) return
    const t = text.trim()
    if (!t) return
    const base = speechBaseRef.current.trim()
    setContent(() => {
      if (!base) return t
      if (base === t || base.endsWith(t)) return base
      return `${base} ${t}`
    })
    setSpeechError(null)
  }, [])

  const speech = useSpeechInput({
    transcribeUrl: speechTranscribeUrl,
    configUrl: speechConfigUrl,
    disabled,
    language: i18n.language?.startsWith('zh') ? 'zh-CN' : 'en-US',
    messages: speechMessages,
    onTranscript: appendTranscript,
    onError: (msg) => setSpeechError(msg),
  })

  const speechEnabled =
    !!speechTranscribeUrl || !!speechConfigUrl || speech.supported

  useEffect(() => {
    if (speech.isListening && !wasListeningRef.current) {
      speechBaseRef.current = content.trimEnd()
    }
    wasListeningRef.current = speech.isListening
  }, [speech.isListening, content])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [content, speech.interimText])

  const handleSubmit = () => {
    const trimmed = content.trim()
    if (!trimmed && !selectedFile) return
    if (speech.isListening) speech.stopListening()
    onSend(trimmed, selectedFile ?? undefined)
    setContent('')
    setSelectedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items
    if (items) {
      for (const item of Array.from(items)) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            setSelectedFile(file)
          }
          break
        }
      }
    }
  }

  const inputValue =
    speech.isListening && speech.interimText
      ? [speechBaseRef.current, speech.interimText].filter(Boolean).join(' ')
      : content

  const displayPlaceholder = speech.isListening
    ? t('chat.listeningPlaceholder')
    : (placeholder ?? t('chat.inputPlaceholder'))

  return (
    <div
      className={cn(
        'border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800',
        compact ? 'px-3 py-2.5' : 'px-4 py-3',
      )}
    >
      {speechError && (
        <p className="text-xs text-amber-600 dark:text-amber-400 mb-2">{speechError}</p>
      )}

      {selectedFile && (
        <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg">
          {selectedFile.type.startsWith('image/') ? (
            <img
              src={URL.createObjectURL(selectedFile)}
              alt=""
              className="w-10 h-10 rounded object-cover shrink-0"
              onLoad={(e) => URL.revokeObjectURL((e.target as HTMLImageElement).src)}
            />
          ) : (
            <Paperclip className="w-4 h-4 text-gray-400 shrink-0" />
          )}
          <span className="text-sm text-gray-600 dark:text-gray-300 truncate flex-1">
            {selectedFile.name}
          </span>
          <button
            type="button"
            onClick={() => {
              setSelectedFile(null)
              if (fileInputRef.current) fileInputRef.current.value = ''
            }}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="flex items-end gap-2">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:text-gray-300 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          title={t('chat.uploadAttachment')}
        >
          <Paperclip className="w-5 h-5" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept="image/*,.pdf,.doc,.docx,.txt"
        />

        {speechEnabled && (
          <button
            type="button"
            onClick={speech.toggleListening}
            disabled={disabled}
            title={speech.isListening ? t('chat.stopVoice') : t('chat.voiceInput')}
            className={cn(
              'p-2 rounded-lg transition-colors disabled:opacity-50',
              speech.isListening
                ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400 animate-pulse'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:text-gray-300 dark:hover:bg-gray-700',
            )}
          >
            {speech.isListening ? (
              <Square className="w-5 h-5" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
          </button>
        )}

        <div className="flex-1 min-w-0">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => {
              const v = e.target.value
              if (speech.isListening) {
                speechBaseRef.current = v.replace(speech.interimText, '').trimEnd()
              } else {
                setContent(v)
              }
            }}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder={displayPlaceholder}
            disabled={disabled}
            rows={1}
            className={cn(
              'block w-full min-h-[42px] h-auto resize-none rounded-xl border border-gray-300 bg-gray-50 px-4 py-2.5 text-sm',
              'placeholder:text-gray-400',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder:text-gray-500',
              speech.isListening && 'ring-2 ring-red-300 dark:ring-red-700',
            )}
          />
        </div>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || (!content.trim() && !selectedFile)}
          className={cn(
            'p-2.5 rounded-xl transition-colors',
            content.trim() || selectedFile
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500 cursor-not-allowed',
          )}
          title={t('chat.send')}
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
