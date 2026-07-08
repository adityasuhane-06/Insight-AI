import { useState, useEffect, useCallback } from 'react'
import { useParams, useLocation, Link } from 'react-router-dom'
import {
  ArrowLeft, Play, Building2, ExternalLink,
  AlertCircle, CheckCircle, RotateCcw
} from 'lucide-react'
import { sessionsApi, type Session } from '../lib/api'
import { useSSE, type SSEEvent } from '../hooks/useSSE'
import WorkflowProgress from '../components/WorkflowProgress'
import ReportViewer from '../components/ReportViewer'
import ChatPanel from '../components/ChatPanel'
import styles from './SessionDetail.module.css'

const STATUS_BADGE = {
  pending: 'badge-pending',
  running: 'badge-running',
  completed: 'badge-completed',
  failed: 'badge-failed',
}

type Tab = 'progress' | 'report' | 'chat'

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()

  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<Tab>('progress')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamLog, setStreamLog] = useState<SSEEvent[]>([])

  const loadSession = useCallback(async () => {
    if (!id) return
    try {
      const s = await sessionsApi.get(id)
      setSession(s)
      // Auto-select tab based on status
      if (s.status === 'completed') setTab('report')
      else if (s.status === 'running') setTab('progress')
    } catch {
      setError('Session not found')
    } finally {
      setLoading(false)
    }
  }, [id])

  // SSE integration
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    setStreamLog(prev => [...prev, event])

    setSession(prev => {
      if (!prev) return prev
      const updated = { ...prev }
      if (event.type === 'progress') {
        updated.status = 'running'
        updated.current_node = event.node || prev.current_node
        if (event.retry_count !== undefined) updated.retry_count = event.retry_count
        if (event.quality_score !== undefined) updated.quality_score = event.quality_score
      }
      if (event.type === 'complete') {
        updated.status = (event.status as Session['status']) || 'completed'
        if (event.quality_score !== undefined) updated.quality_score = event.quality_score
      }
      if (event.type === 'error') {
        updated.status = 'failed'
        updated.error_message = event.message || 'Unknown error'
      }
      return updated
    })
  }, [])

  const handleSSEComplete = useCallback(async () => {
    setIsStreaming(false)
    // Reload session to get full report
    if (id) {
      const s = await sessionsApi.get(id)
      setSession(s)
      if (s.status === 'completed') setTab('report')
    }
  }, [id])

  const { connect } = useSSE(
    id ?? null,
    {
      onEvent: handleSSEEvent,
      onComplete: handleSSEComplete,
    }
  )

  useEffect(() => { loadSession() }, [loadSession])

  // Auto-start if navigated from new session form
  useEffect(() => {
    if (location.state?.autoStart && session?.status === 'pending') {
      startWorkflow()
    }
  }, [session?.status, location.state])

  const startWorkflow = () => {
    if (!session || isStreaming) return
    setIsStreaming(true)
    setStreamLog([])
    setTab('progress')
    connect()
  }

  if (loading) {
    return (
      <div className="container">
        <div className={styles.loadingState}>
          <div className="spinner spinner-lg" />
          <p>Loading session...</p>
        </div>
      </div>
    )
  }

  if (error || !session) {
    return (
      <div className="container">
        <div className={styles.errorState}>
          <AlertCircle size={48} />
          <h2>Session not found</h2>
          <Link to="/" className="btn btn-secondary">
            <ArrowLeft size={15} /> Back to Sessions
          </Link>
        </div>
      </div>
    )
  }

  const canStart = session.status === 'pending' || session.status === 'failed'
  const isRunning = session.status === 'running' || isStreaming
  const isComplete = session.status === 'completed'

  return (
    <div className="container">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className={styles.pageHeader}>
        <Link to="/" className="btn btn-ghost btn-sm">
          <ArrowLeft size={15} /> Sessions
        </Link>

        <div className={styles.titleRow}>
          <div className={styles.companyIcon}>
            <Building2 size={20} />
          </div>
          <div className={styles.titleInfo}>
            <h1 className={styles.title}>{session.company_name}</h1>
            <div className={styles.meta}>
              <a href={session.website} target="_blank" rel="noopener noreferrer" className={styles.website}>
                <ExternalLink size={12} />
                {session.website.replace(/^https?:\/\//, '').slice(0, 50)}
              </a>
              <span className={`badge ${STATUS_BADGE[session.status]}`}>
                {session.status}
                {isStreaming && session.status !== 'completed' && (
                  <span className={styles.pulseDot} />
                )}
              </span>
              {isComplete && session.quality_score > 0 && (
                <span className={styles.qualityBadge}>
                  <CheckCircle size={12} />
                  {Math.round(session.quality_score * 100)}% quality
                </span>
              )}
            </div>
          </div>
        </div>

        <p className={styles.objective}>{session.objective}</p>

        <div className={styles.actions}>
          {canStart && (
            <button
              className="btn btn-primary"
              onClick={startWorkflow}
              disabled={isRunning}
              id="start-workflow-btn"
            >
              <Play size={15} />
              {session.status === 'failed' ? 'Retry Research' : 'Start Research'}
            </button>
          )}
          {isRunning && (
            <span className={styles.runningIndicator}>
              <div className="spinner" />
              Research in progress...
            </span>
          )}
          {isComplete && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setSession(prev => prev ? { ...prev, status: 'pending' } : prev)
              }}
              id="redo-research-btn"
              title="Reset and redo research"
            >
              <RotateCcw size={14} /> Redo
            </button>
          )}
        </div>
      </div>

      <div className={styles.layout}>
        {/* ── Left: Workflow + Tabs ───────────────────────────── */}
        <div className={styles.main}>
          {/* Tabs */}
          <div className="tabs">
            <button
              className={`tab ${tab === 'progress' ? 'active' : ''}`}
              onClick={() => setTab('progress')}
              id="tab-progress"
            >
              Workflow
            </button>
            <button
              className={`tab ${tab === 'report' ? 'active' : ''}`}
              onClick={() => setTab('report')}
              disabled={!isComplete && !session.report_markdown}
              id="tab-report"
            >
              Report {isComplete && '✓'}
            </button>
            <button
              className={`tab ${tab === 'chat' ? 'active' : ''}`}
              onClick={() => setTab('chat')}
              disabled={!isComplete}
              id="tab-chat"
            >
              Chat {isComplete && '💬'}
            </button>
          </div>

          {/* Tab content */}
          {tab === 'progress' && (
            <div className={styles.tabContent}>
              <WorkflowProgress
                currentNode={session.current_node}
                sessionStatus={session.status}
                retryCount={session.retry_count}
                qualityScore={session.quality_score}
              />

              {/* Stream log */}
              {streamLog.length > 0 && (
                <div className={styles.streamLog}>
                  <h4 className={styles.logTitle}>Live Log</h4>
                  {streamLog.map((ev, i) => (
                    <div key={i} className={`${styles.logEntry} ${styles[`log-${ev.type}`]}`}>
                      <span className={styles.logType}>{ev.type}</span>
                      <span>{ev.description || ev.message || ev.node}</span>
                    </div>
                  ))}
                </div>
              )}

              {session.error_message && (
                <div className={styles.errorCard}>
                  <AlertCircle size={16} />
                  <div>
                    <strong>Error</strong>
                    <p>{session.error_message}</p>
                  </div>
                </div>
              )}

              {!isRunning && canStart && (
                <div className={styles.pendingCard}>
                  <Play size={24} />
                  <div>
                    <h3>Ready to Research</h3>
                    <p>Click "Start Research" to run the LangGraph AI workflow</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === 'report' && session.report_markdown && (
            <div className={`${styles.tabContent} fade-in`}>
              <ReportViewer
                reportMarkdown={session.report_markdown}
                reportJson={session.report_json}
              />
            </div>
          )}

          {tab === 'chat' && isComplete && (
            <div className={`${styles.tabContent} ${styles.chatTabContent} fade-in`}>
              <ChatPanel sessionId={session.id} companyName={session.company_name} />
            </div>
          )}
        </div>

        {/* ── Right: Chat sidebar (always visible when complete) ── */}
        {isComplete && tab !== 'chat' && (
          <div className={`${styles.sidebar} fade-in`}>
            <ChatPanel sessionId={session.id} companyName={session.company_name} />
          </div>
        )}
      </div>
    </div>
  )
}
