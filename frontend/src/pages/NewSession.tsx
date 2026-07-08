import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Building2, Globe, Target, Loader2 } from 'lucide-react'
import { sessionsApi } from '../lib/api'
import styles from './NewSession.module.css'

const OBJECTIVE_SUGGESTIONS = [
  'Prepare for an initial sales discovery call',
  'Research for a partnership opportunity',
  'Competitive intelligence and analysis',
  'Prepare for a follow-up deal closing meeting',
  'Account-based marketing research',
]

export default function NewSession() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    company_name: '',
    website: '',
    objective: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  const validate = () => {
    const e: Record<string, string> = {}
    if (!form.company_name.trim()) e.company_name = 'Company name is required'
    if (!form.website.trim()) e.website = 'Website is required'
    else if (!/^https?:\/\/.+/.test(form.website)) e.website = 'Enter a valid URL starting with http:// or https://'
    if (!form.objective.trim()) e.objective = 'Research objective is required'
    else if (form.objective.trim().length < 10) e.objective = 'Please describe your objective in at least 10 characters'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    setApiError('')
    try {
      const session = await sessionsApi.create(form)
      navigate(`/sessions/${session.id}`, { state: { autoStart: true } })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create session'
      setApiError(msg)
    } finally {
      setLoading(false)
    }
  }

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm(f => ({ ...f, [key]: e.target.value }))
    if (errors[key]) setErrors(prev => ({ ...prev, [key]: '' }))
  }

  return (
    <div className="container">
      <div className={styles.page}>
        {/* Back button */}
        <Link to="/" className="btn btn-ghost btn-sm" style={{ alignSelf: 'flex-start' }}>
          <ArrowLeft size={15} />
          Back to Sessions
        </Link>

        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.cardIcon}>
              <Building2 size={24} />
            </div>
            <div>
              <h1 className={styles.title}>New Research Session</h1>
              <p className={styles.subtitle}>
                Enter the company details and your research objective to get started.
              </p>
            </div>
          </div>

          {apiError && (
            <div className={styles.errorBanner} role="alert">
              {apiError}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form} id="new-session-form" noValidate>
            {/* Company Name */}
            <div className="form-group">
              <label className="form-label" htmlFor="company-name">
                <Building2 size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                Company Name <span>*</span>
              </label>
              <input
                id="company-name"
                type="text"
                className={`form-input ${errors.company_name ? styles.inputError : ''}`}
                placeholder="e.g. Salesforce, HubSpot, Notion..."
                value={form.company_name}
                onChange={set('company_name')}
                disabled={loading}
                autoFocus
              />
              {errors.company_name && <span className={styles.fieldError}>{errors.company_name}</span>}
            </div>

            {/* Website */}
            <div className="form-group">
              <label className="form-label" htmlFor="website">
                <Globe size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                Company Website <span>*</span>
              </label>
              <input
                id="website"
                type="url"
                className={`form-input ${errors.website ? styles.inputError : ''}`}
                placeholder="https://www.example.com"
                value={form.website}
                onChange={set('website')}
                disabled={loading}
              />
              {errors.website && <span className={styles.fieldError}>{errors.website}</span>}
            </div>

            {/* Research Objective */}
            <div className="form-group">
              <label className="form-label" htmlFor="objective">
                <Target size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                Research Objective <span>*</span>
              </label>
              <textarea
                id="objective"
                className={`form-textarea ${errors.objective ? styles.inputError : ''}`}
                placeholder="Describe what you want to accomplish with this research..."
                value={form.objective}
                onChange={set('objective')}
                disabled={loading}
                rows={3}
              />
              {errors.objective && <span className={styles.fieldError}>{errors.objective}</span>}

              {/* Suggestions */}
              <div className={styles.suggestions}>
                <span className={styles.suggestionsLabel}>Quick fill:</span>
                {OBJECTIVE_SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    type="button"
                    className={styles.chip}
                    onClick={() => {
                      setForm(f => ({ ...f, objective: s }))
                      if (errors.objective) setErrors(prev => ({ ...prev, objective: '' }))
                    }}
                    disabled={loading}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Info box */}
            <div className={styles.infoBox}>
              <div className={styles.infoItem}><span>🔍</span> Web search via Tavily or DuckDuckGo</div>
              <div className={styles.infoItem}><span>🤖</span> LangGraph multi-node AI workflow</div>
              <div className={styles.infoItem}><span>📊</span> 9-section structured briefing</div>
              <div className={styles.infoItem}><span>💬</span> Follow-up AI Q&A</div>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg btn-full"
              disabled={loading}
              id="submit-new-session"
            >
              {loading ? (
                <><Loader2 size={18} className={styles.spin} /> Creating session...</>
              ) : (
                <><Building2 size={18} /> Start Research</>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
