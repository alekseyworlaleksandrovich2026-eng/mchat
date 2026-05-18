import React, { useEffect, useState, useCallback } from 'react'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastData {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
}

let toastListeners: Array<(toast: ToastData) => void> = []
let toastId = 0

export function toast(
  title: string,
  options?: {
    type?: ToastType
    message?: string
    duration?: number
  },
) {
  const id = `toast-${++toastId}`
  const data: ToastData = {
    id,
    type: options?.type || 'info',
    title,
    message: options?.message,
    duration: options?.duration || 4000,
  }
  toastListeners.forEach((listener) => listener(data))
}

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
}

const styles = {
  success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/50 dark:border-green-800 dark:text-green-300',
  error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/50 dark:border-red-800 dark:text-red-300',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/50 dark:border-yellow-800 dark:text-yellow-300',
  info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/50 dark:border-blue-800 dark:text-blue-300',
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastData[]>([])

  const addToast = useCallback((data: ToastData) => {
    setToasts((prev) => [...prev, data])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  useEffect(() => {
    toastListeners.push(addToast)
    return () => {
      toastListeners = toastListeners.filter((l) => l !== addToast)
    }
  }, [addToast])

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onClose={() => removeToast(t.id)} />
      ))}
    </div>
  )
}

function ToastItem({ toast: t, onClose }: { toast: ToastData; onClose: () => void }) {
  const Icon = icons[t.type]

  useEffect(() => {
    if (t.duration && t.duration > 0) {
      const timer = setTimeout(onClose, t.duration)
      return () => clearTimeout(timer)
    }
  }, [t.duration, onClose])

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border shadow-lg',
        styles[t.type],
        'animate-[slideInRight_0.3s_ease-out]',
      )}
    >
      <Icon className="w-5 h-5 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{t.title}</p>
        {t.message && (
          <p className="text-sm mt-1 opacity-80">{t.message}</p>
        )}
      </div>
      <button
        onClick={onClose}
        className="shrink-0 p-0.5 rounded hover:opacity-70 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}
