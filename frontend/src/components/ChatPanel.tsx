import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { chatApi, type ChatMessage } from '../lib/api'
import styles from './ChatPanel.module.css'

interface Props {
  sessionId: string
  companyName: string
}

export default function ChatPanel({ sessionId, companyName }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatApi.getHistory(sessionId)
      .then(setMessages)
      .catch(() => setError('Could not load chat history'))
      .finally(() => setLoading(false))
  }, [sessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || sending) return

    setInput('')
    setSending(true)
    setError('')

    // Optimistic update
    const tempMsg: ChatMessage = {
      id: 'temp-' + Date.now(),
      session_id: sessionId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempMsg])

    try {
      const reply = await chatApi.sendMessage(sessionId, text)
      // Replace temp with real user message + add assistant reply
      setMessages(prev => {
        const without = prev.filter(m => m.id !== tempMsg.id)
        return [...without, { ...tempMsg, id: 'user-' + reply.id }, reply]
      })
    } catch {
      setError('Failed to send message. Please try again.')
      setMessages(prev => prev.filter(m => m.id !== tempMsg.id))
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const SUGGESTIONS = [
    `Who are ${companyName}'s main competitors?`,
    `What's the best angle for our outreach?`,
    `What are the biggest red flags?`,
    `Summarize the key business signals`,
  ]

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <Bot size={16} />
        <span>AI Research Assistant</span>
        <span className={styles.hint}>Ask anything about {companyName}</span>
      </div>

      <div className={styles.messages} id="chat-messages">
        {loading ? (
          <div className={styles.center}><div className="spinner" /></div>
        ) : messages.length === 0 ? (
          <div className={styles.welcome}>
            <Bot size={32} strokeWidth={1.5} />
            <h4>Ask me about {companyName}</h4>
            <p>I have full context of the research report. Ask me anything.</p>
            <div className={styles.suggestions}>
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  className={styles.suggestion}
                  onClick={() => setInput(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map(msg => (
            <div
              key={msg.id}
              className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.assistantMessage} fade-in`}
            >
              <div className={styles.avatar}>
                {msg.role === 'user' ? <User size={13} /> : <Bot size={13} />}
              </div>
              <div className={styles.bubble}>
                <p>{msg.content}</p>
                <span className={styles.time}>
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))
        )}

        {sending && (
          <div className={`${styles.message} ${styles.assistantMessage}`}>
            <div className={styles.avatar}><Bot size={13} /></div>
            <div className={`${styles.bubble} ${styles.typing}`}>
              <Loader2 size={14} className={styles.spin} />
              <span>Thinking...</span>
            </div>
          </div>
        )}

        {error && <p className={styles.error}>{error}</p>}
        <div ref={bottomRef} />
      </div>

      <div className={styles.inputArea}>
        <textarea
          className={`form-textarea ${styles.textarea}`}
          placeholder={`Ask about ${companyName}...`}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          disabled={sending}
          id="chat-input"
        />
        <button
          className={`btn btn-primary btn-icon ${styles.sendBtn}`}
          onClick={sendMessage}
          disabled={!input.trim() || sending}
          id="chat-send-btn"
        >
          {sending ? <Loader2 size={16} className={styles.spin} /> : <Send size={16} />}
        </button>
      </div>
    </div>
  )
}
