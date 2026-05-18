import { useEffect, useState } from 'react'

/** Throttle fast updates (e.g. streaming tokens) for cheaper ReactMarkdown re-renders. */
export function useThrottledValue<T>(value: T, delayMs = 50): T {
  const [throttled, setThrottled] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setThrottled(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])

  return throttled
}
