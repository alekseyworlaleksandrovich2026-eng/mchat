import React from 'react'
import { Bot, Headphones, MessageCircle, Sparkles, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface WidgetButtonProps {
  isOpen: boolean
  onClick: () => void
  position: 'right' | 'left'
  primaryColor?: string
  launcherIcon?: string
  launcherText?: string
}

function resolveLauncherIcon(name?: string) {
  const normalized = (name || '').toLowerCase()
  if (normalized === 'bot' || normalized === 'robot') return Bot
  if (normalized === 'spark' || normalized === 'sparkles') return Sparkles
  if (normalized === 'support' || normalized === 'headset') return Headphones
  if (normalized === 'message' || normalized === 'chat') return MessageCircle
  return MessageCircle
}

export function WidgetButton({
  isOpen,
  onClick,
  position,
  primaryColor = '#3b82f6',
  launcherIcon = 'chat',
  launcherText = '',
}: WidgetButtonProps) {
  const LauncherIcon = resolveLauncherIcon(launcherIcon)
  const showText = !isOpen && launcherText.trim().length > 0

  return (
    <button
      onClick={onClick}
      className={cn(
        'fixed bottom-6 z-[9999] shadow-lg flex items-center justify-center gap-2 transition-all duration-300 hover:scale-105 hover:shadow-xl',
        showText
          ? 'h-12 px-4 rounded-full'
          : 'w-14 h-14 rounded-full',
        position === 'right' ? 'right-6' : 'left-6',
      )}
      style={{ backgroundColor: primaryColor }}
    >
      {isOpen ? (
        <X className="w-6 h-6 text-white" />
      ) : (
        <>
          <LauncherIcon className={cn('text-white', showText ? 'w-5 h-5' : 'w-6 h-6')} />
          {showText && <span className="text-sm font-medium text-white">{launcherText}</span>}
        </>
      )}
    </button>
  )
}
