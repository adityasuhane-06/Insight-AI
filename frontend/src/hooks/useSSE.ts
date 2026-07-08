import { useEffect, useRef, useCallback } from 'react'
import { getStreamUrl } from '../lib/api'

export interface SSEEvent {
  type: 'start' | 'progress' | 'complete' | 'error'
  node?: string
  description?: string
  message?: string
  status?: string
  quality_score?: number
  retry_count?: number
  data?: Record<string, unknown>
}

interface UseSSEOptions {
  onEvent: (event: SSEEvent) => void
  onError?: (error: Event) => void
  onComplete?: () => void
}

export function useSSE(sessionId: string | null, { onEvent, onError, onComplete }: UseSSEOptions) {
  const esRef = useRef<EventSource | null>(null)
  const activeRef = useRef(false)

  const connect = useCallback(() => {
    if (!sessionId || activeRef.current) return
    activeRef.current = true

    const url = getStreamUrl(sessionId)
    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (e: MessageEvent) => {
      try {
        const event: SSEEvent = JSON.parse(e.data)
        onEvent(event)

        if (event.type === 'complete' || event.type === 'error') {
          es.close()
          esRef.current = null
          activeRef.current = false
          onComplete?.()
        }
      } catch {
        console.error('SSE parse error:', e.data)
      }
    }

    es.onerror = (e) => {
      console.error('SSE connection error:', e)
      es.close()
      esRef.current = null
      activeRef.current = false
      onError?.(e)
      onComplete?.()
    }
  }, [sessionId, onEvent, onError, onComplete])

  const disconnect = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
    activeRef.current = false
  }, [])

  useEffect(() => {
    return () => { disconnect() }
  }, [disconnect])

  return { connect, disconnect, isActive: activeRef.current }
}
