import { Github } from 'lucide-react'
import { cn } from '@/lib/utils'

export const MCHAT_GITHUB_URL = 'https://github.com/windinwing/mchat'

interface GithubLinkProps {
  className?: string
  iconClassName?: string
  /** Light text on colored headers (widget) */
  onDark?: boolean
}

export function GithubLink({
  className,
  iconClassName,
  onDark = false,
}: GithubLinkProps) {
  return (
    <a
      href={MCHAT_GITHUB_URL}
      target="_blank"
      rel="noopener noreferrer"
      title="GitHub"
      className={cn(
        'inline-flex items-center justify-center rounded-lg p-1.5 transition-colors',
        onDark
          ? 'text-white/80 hover:text-white hover:bg-white/15'
          : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700',
        className,
      )}
    >
      <Github className={cn('w-4 h-4', iconClassName)} />
    </a>
  )
}
