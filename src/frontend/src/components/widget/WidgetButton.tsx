import React from 'react'
import { MessageCircle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface WidgetButtonProps {
  isOpen: boolean
  onClick: () => void
  position: 'right' | 'left'
  primaryColor?: string
}

export function WidgetButton({
  isOpen,
  onClick,
  position,
  primaryColor = '#3b82f6',
}: WidgetButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'fixed bottom-6 z-[9999] w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300 hover:scale-110 hover:shadow-xl',
        position === 'right' ? 'right-6' : 'left-6',
      )}
      style={{ backgroundColor: primaryColor }}
    >
      {isOpen ? (
        <X className="w-6 h-6 text-white" />
      ) : (
        <MessageCircle className="w-6 h-6 text-white" />
      )}
    </button>
  )
}
