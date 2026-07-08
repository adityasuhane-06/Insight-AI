import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Building2, ExternalLink, Trash2, Clock, Zap, TrendingUp, CheckCircle } from 'lucide-react'
import { sessionsApi, type SessionListItem } from '../lib/api'
import styles from './Home.module.css'

const STATUS_BADGE = {
  pending: 'badge-pending',
  running: 'badge-running',
  completed: 'badge-completed',
  failed: 'badge-failed',
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function Home() {
  const [sessions, setSessions] = useState<SessionListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    sessionsApi.list()
      .then(setSessions)
      .catch(() => setError('Failed to load sessions'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm('Delete this research session?')) return
    setDeleting(id)
    try {
      await sessionsApi.delete(id)
      setSessions(prev => prev.filter(s => s.id !== id))
    } catch {
      setError('Failed to delete session')
    } finally {
      setDeleting(null)
    }
  }

  const completed = sessions.filter(s => s.status === 'completed').length
  const running = sessions.filter(s => s.status === 'running').length

  return (
    <div className="container">
      {/* ── Hero ─────────────────────────────────────────────────── */}
      <div className={styles.hero}>
        <div className={styles.heroIcon}>
          <Zap size={28} />
        </div>
        <h1 className={styles.heroTitle}>
          AI Research <span className="gradient-text">Copilot</span>
        </h1>
        <p className={styles.heroSub}>
          Prepare for any sales or business meeting with AI-powered company research,
          structured briefings, and intelligent follow-up Q&A.
        </p>
        <Link to="/new" className="btn btn-primary btn-lg" id="hero-new-session-btn">
          <Plus size={18} />
          Start New Research
        </Link>
      </div>

      {/* ── Stats ────────────────────────────────────────────────── */}
      {sessions.length > 0 && (
        <div className={styles.stats}>
          <div className={styles.stat}>
            <TrendingUp size={20} />
            <div>
              <span className={styles.statNum}>{sessions.length}</span>
              <span className={styles.statLabel}>Total Sessions</span>
            </div>
          </div>
          <div className={styles.stat}>
            <CheckCircle size={20} style={{ color: 'var(--color-accent-green)' }} />
            <div>
              <span className={styles.statNum}>{completed}</span>
              <span className={styles.statLabel}>Completed</span>
            </div>
          </div>
          <div className={styles.stat}>
            <div className="spinner" style={{ borderTopColor: 'var(--color-accent-cyan)' }} />
            <div>
              <span className={styles.statNum}>{running}</span>
              <span className={styles.statLabel}>Running</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Sessions list ─────────────────────────────────────────── */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2>Research Sessions</h2>
          <button className="btn btn-secondary btn-sm" onClick={load} id="refresh-btn">
            Refresh
          </button>
        </div>

        {error && <div className={styles.errorBanner}>{error}</div>}

        {loading ? (
          <div className={styles.loadingState}>
            <div className="spinner spinner-lg" />
            <p>Loading sessions...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="empty-state">
            <Building2 size={48} />
            <h3>No research sessions yet</h3>
            <p>Create your first research session to get started.</p>
            <Link to="/new" className="btn btn-primary" id="empty-new-btn">
              <Plus size={16} />
              New Research Session
            </Link>
          </div>
        ) : (
          <div className={styles.grid}>
            {sessions.map(session => (
              <Link
                key={session.id}
                to={`/sessions/${session.id}`}
                className={styles.sessionCard}
                id={`session-card-${session.id}`}
              >
                <div className={styles.cardTop}>
                  <div className={styles.cardIcon}>
                    <Building2 size={18} />
                  </div>
                  <div className={styles.cardInfo}>
                    <h3 className={styles.cardTitle}>{session.company_name}</h3>
                    <a
                      href={session.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.cardWebsite}
                      onClick={e => e.stopPropagation()}
                    >
                      <ExternalLink size={11} />
                      {session.website.replace(/^https?:\/\//, '').slice(0, 40)}
                    </a>
                  </div>
                  <span className={`badge ${STATUS_BADGE[session.status]}`}>
                    {session.status}
                  </span>
                </div>

                <p className={styles.cardObjective}>{session.objective}</p>

                <div className={styles.cardFooter}>
                  <span className={styles.cardTime}>
                    <Clock size={12} />
                    {timeAgo(session.updated_at)}
                  </span>
                  {session.status === 'completed' && session.quality_score > 0 && (
                    <span className={styles.cardScore}>
                      {Math.round(session.quality_score * 100)}% quality
                    </span>
                  )}
                  <button
                    className="btn btn-icon btn-ghost btn-sm"
                    onClick={e => handleDelete(e, session.id)}
                    disabled={deleting === session.id}
                    title="Delete session"
                    id={`delete-session-${session.id}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
