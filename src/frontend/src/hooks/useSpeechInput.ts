import { useCallback, useEffect, useRef, useState } from 'react'

export interface SpeechConfig {
  enabled: boolean
  provider: string
  browser_fallback: boolean
  max_audio_mb: number
  language: string
}

export interface SpeechMessages {
  browserUnsupported: string
  recognitionFailed: string
  recordingTooShort: string
  transcribeFailed: string
  noSpeechDetected: string
  speechFailed: string
  micDenied: string
  unavailable: string
}

interface UseSpeechInputOptions {
  /** e.g. /api/speech/transcribe or /api/widget/{id}/speech/transcribe */
  transcribeUrl?: string
  /** e.g. /api/speech/config */
  configUrl?: string
  disabled?: boolean
  language?: string
  messages: SpeechMessages
  onTranscript: (text: string, interim?: boolean) => void
  onError?: (message: string) => void
}

function getSpeechRecognitionCtor():
  | (new () => SpeechRecognition)
  | undefined {
  const w = window as Window & {
    SpeechRecognition?: new () => SpeechRecognition
    webkitSpeechRecognition?: new () => SpeechRecognition
  }
  return w.SpeechRecognition || w.webkitSpeechRecognition
}

async function fetchSpeechConfig(url: string): Promise<SpeechConfig | null> {
  try {
    const res = await fetch(url)
    if (!res.ok) return null
    return (await res.json()) as SpeechConfig
  } catch {
    return null
  }
}

export function useSpeechInput({
  transcribeUrl,
  configUrl,
  disabled = false,
  language = 'zh-CN',
  messages,
  onTranscript,
  onError,
}: UseSpeechInputOptions) {
  const [isListening, setIsListening] = useState(false)
  const [mode, setMode] = useState<'browser' | 'recorder' | 'off'>('off')
  const [interimText, setInterimText] = useState('')

  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const configRef = useRef<SpeechConfig | null>(null)
  const transcriptDeliveredRef = useRef(false)
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  useEffect(() => {
    if (!configUrl) {
      const Ctor = getSpeechRecognitionCtor()
      setMode(Ctor ? 'browser' : 'off')
      return
    }
    let cancelled = false
    fetchSpeechConfig(configUrl).then((cfg) => {
      if (cancelled) return
      configRef.current = cfg
      const Ctor = getSpeechRecognitionCtor()
      if (cfg?.enabled && transcribeUrl) {
        setMode('recorder')
      } else if (cfg?.browser_fallback !== false && Ctor) {
        setMode('browser')
      } else if (Ctor) {
        setMode('browser')
      } else {
        setMode('off')
      }
    })
    return () => {
      cancelled = true
    }
  }, [configUrl, transcribeUrl])

  const stopBrowser = useCallback(() => {
    recognitionRef.current?.stop()
    recognitionRef.current = null
    setIsListening(false)
    setInterimText('')
  }, [])

  const stopRecorder = useCallback(() => {
    const rec = mediaRecorderRef.current
    if (rec && rec.state !== 'inactive') {
      rec.stop()
    }
    mediaRecorderRef.current = null
  }, [])

  const startBrowser = useCallback(() => {
    const Ctor = getSpeechRecognitionCtor()
    const msg = messagesRef.current
    if (!Ctor) {
      onError?.(msg.browserUnsupported)
      return
    }
    const recognition = new Ctor()
    recognition.lang = language
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    let finalText = ''
    transcriptDeliveredRef.current = false

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0]?.transcript || ''
        if (event.results[i].isFinal) {
          finalText += t
        } else {
          interim += t
        }
      }
      setInterimText((finalText + interim).trim())
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error !== 'aborted') {
        onError?.(
          msg.recognitionFailed.replace('{{error}}', event.error),
        )
      }
      setIsListening(false)
      setInterimText('')
    }

    recognition.onend = () => {
      setIsListening(false)
      setInterimText('')
      const text = finalText.trim()
      if (text && !transcriptDeliveredRef.current) {
        transcriptDeliveredRef.current = true
        onTranscript(text, false)
      }
      recognitionRef.current = null
    }

    recognitionRef.current = recognition
    recognition.start()
    setIsListening(true)
  }, [language, onError, onTranscript])

  const startRecorder = useCallback(async () => {
    const msg = messagesRef.current
    if (!transcribeUrl) {
      startBrowser()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/mp4'

      const recorder = new MediaRecorder(stream, { mimeType })
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      transcriptDeliveredRef.current = false

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        setIsListening(false)
        const blob = new Blob(chunksRef.current, { type: mimeType })
        chunksRef.current = []
        if (blob.size < 500) {
          onError?.(msg.recordingTooShort)
          return
        }
        const ext = mimeType.includes('webm') ? 'webm' : 'm4a'
        const form = new FormData()
        form.append('file', blob, `recording.${ext}`)
        try {
          const res = await fetch(transcribeUrl, {
            method: 'POST',
            body: form,
          })
          if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            const detail =
              typeof err.detail === 'string'
                ? err.detail
                : msg.transcribeFailed
            throw new Error(detail)
          }
          const data = (await res.json()) as { text?: string }
          const text = data.text?.trim() || ''
          if (text && !transcriptDeliveredRef.current) {
            transcriptDeliveredRef.current = true
            onTranscript(text, false)
          } else if (!text) {
            onError?.(msg.noSpeechDetected)
          }
        } catch (e) {
          onError?.(e instanceof Error ? e.message : msg.speechFailed)
        }
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setIsListening(true)
    } catch (e) {
      onError?.(e instanceof Error ? e.message : msg.micDenied)
    }
  }, [onError, onTranscript, startBrowser, transcribeUrl])

  const startListening = useCallback(() => {
    if (disabled || isListening) return
    const msg = messagesRef.current
    if (mode === 'off') {
      const Ctor = getSpeechRecognitionCtor()
      if (Ctor) {
        startBrowser()
      } else {
        onError?.(msg.unavailable)
      }
      return
    }
    if (mode === 'browser') {
      startBrowser()
    } else {
      void startRecorder()
    }
  }, [disabled, isListening, mode, onError, startBrowser, startRecorder])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      stopBrowser()
      return
    }
    if (mediaRecorderRef.current) {
      stopRecorder()
    }
  }, [stopBrowser, stopRecorder])

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [isListening, startListening, stopListening])

  useEffect(() => {
    return () => {
      stopBrowser()
      stopRecorder()
    }
  }, [stopBrowser, stopRecorder])

  return {
    isListening,
    interimText,
    mode,
    toggleListening,
    startListening,
    stopListening,
    supported: mode !== 'off' || !!getSpeechRecognitionCtor(),
  }
}
