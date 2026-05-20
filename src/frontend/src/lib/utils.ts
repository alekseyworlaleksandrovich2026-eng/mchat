import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

const ISO_WITHOUT_TIMEZONE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$/

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function parseDate(value: string | Date | number): Date {
  if (value instanceof Date) return new Date(value.getTime())
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (ISO_WITHOUT_TIMEZONE.test(trimmed)) {
      return new Date(`${trimmed}Z`)
    }
  }
  return new Date(value)
}

export function formatDate(date: string | Date): string {
  const d = parseDate(date)
  if (Number.isNaN(d.getTime())) return ''

  const locale =
    document.documentElement.lang ||
    localStorage.getItem('mchat_lang') ||
    navigator.language ||
    'en-US'

  const now = Date.now()
  const diffMs = d.getTime() - now
  const absMs = Math.abs(diffMs)
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })

  if (absMs < 60_000) return rtf.format(Math.round(diffMs / 1000), 'second')
  if (absMs < 3_600_000) return rtf.format(Math.round(diffMs / 60_000), 'minute')
  if (absMs < 86_400_000) return rtf.format(Math.round(diffMs / 3_600_000), 'hour')
  if (absMs < 7 * 86_400_000) return rtf.format(Math.round(diffMs / 86_400_000), 'day')

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(d)
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15)
}

export function classNames(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ')
}
