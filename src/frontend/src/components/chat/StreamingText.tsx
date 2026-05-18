import React, { useState, useEffect, useRef } from 'react'

interface StreamingTextProps {
  content: string
  speed?: number
  onComplete?: () => void
}

export function StreamingText({ content, speed = 20, onComplete }: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState('')
  const indexRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    indexRef.current = 0
    setDisplayedText('')

    if (!content) return

    timerRef.current = setInterval(() => {
      if (indexRef.current < content.length) {
        setDisplayedText(content.slice(0, indexRef.current + 1))
        indexRef.current++
      } else {
        if (timerRef.current) clearInterval(timerRef.current)
        onComplete?.()
      }
    }, speed)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [content, speed, onComplete])

  return (
    <span>
      {displayedText}
      {displayedText.length < content.length && (
        <span className="cursor-blink inline-block w-[2px] h-4 bg-current ml-0.5 align-middle" />
      )}
    </span>
  )
}
