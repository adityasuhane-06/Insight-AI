import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Building2, Package, Users, TrendingUp, AlertTriangle,
  HelpCircle, Mail, Search, Link as LinkIcon
} from 'lucide-react'
import styles from './ReportViewer.module.css'

interface ReportSection {
  key: string
  label: string
  icon: React.ReactNode
  color: string
}

const SECTIONS: ReportSection[] = [
  { key: 'company_overview', label: 'Company Overview', icon: <Building2 size={16} />, color: 'purple' },
  { key: 'products_services', label: 'Products & Services', icon: <Package size={16} />, color: 'cyan' },
  { key: 'target_customers', label: 'Target Customers', icon: <Users size={16} />, color: 'green' },
  { key: 'business_signals', label: 'Business Signals', icon: <TrendingUp size={16} />, color: 'amber' },
  { key: 'risks_challenges', label: 'Risks & Challenges', icon: <AlertTriangle size={16} />, color: 'red' },
  { key: 'discovery_questions', label: 'Discovery Questions', icon: <HelpCircle size={16} />, color: 'purple' },
  { key: 'outreach_strategy', label: 'Outreach Strategy', icon: <Mail size={16} />, color: 'cyan' },
  { key: 'unknowns', label: 'Unknowns & Gaps', icon: <Search size={16} />, color: 'muted' },
  { key: 'sources', label: 'Sources', icon: <LinkIcon size={16} />, color: 'muted' },
]

type ViewMode = 'structured' | 'markdown'

interface Props {
  reportMarkdown: string
  reportJson: string
}

export default function ReportViewer({ reportMarkdown, reportJson }: Props) {
  const [viewMode, setViewMode] = useState<ViewMode>('structured')
  const [activeSection, setActiveSection] = useState<string | null>(null)

  let reportData: Record<string, string | string[]> = {}
  try {
    const parsed = JSON.parse(reportJson)
    reportData = parsed.sections || {}
  } catch {
    viewMode === 'structured' && setViewMode('markdown')
  }

  const renderValue = (key: string, value: string | string[]) => {
    if (Array.isArray(value)) {
      if (key === 'sources') {
        return (
          <ul className={styles.sourceList}>
            {value.map((url, i) => (
              <li key={i}>
                <a href={url} target="_blank" rel="noopener noreferrer" className={styles.sourceLink}>
                  <LinkIcon size={12} />
                  {url.length > 70 ? url.slice(0, 70) + '…' : url}
                </a>
              </li>
            ))}
          </ul>
        )
      }
      return (
        <ol className={styles.questionList}>
          {value.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ol>
      )
    }
    return <p className={styles.sectionText}>{value}</p>
  }

  return (
    <div className={styles.container}>
      {/* View mode toggle */}
      <div className={styles.toolbar}>
        <div className={styles.viewToggle}>
          <button
            className={`${styles.toggleBtn} ${viewMode === 'structured' ? styles.toggleActive : ''}`}
            onClick={() => setViewMode('structured')}
            id="view-structured"
          >
            Structured
          </button>
          <button
            className={`${styles.toggleBtn} ${viewMode === 'markdown' ? styles.toggleActive : ''}`}
            onClick={() => setViewMode('markdown')}
            id="view-markdown"
          >
            Markdown
          </button>
        </div>
      </div>

      {viewMode === 'markdown' ? (
        <div className={styles.markdownBody}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{reportMarkdown}</ReactMarkdown>
        </div>
      ) : (
        <div className={styles.structured}>
          {SECTIONS.map(section => {
            const value = reportData[section.key]
            if (!value || (Array.isArray(value) && value.length === 0)) return null
            const isOpen = activeSection === null || activeSection === section.key

            return (
              <div
                key={section.key}
                className={`${styles.section} ${styles[`section-${section.color}`]}`}
              >
                <button
                  className={styles.sectionHeader}
                  onClick={() => setActiveSection(activeSection === section.key ? null : section.key)}
                  id={`section-${section.key}`}
                >
                  <span className={styles.sectionIcon}>{section.icon}</span>
                  <span className={styles.sectionLabel}>{section.label}</span>
                  <span className={styles.sectionChevron}>{isOpen ? '−' : '+'}</span>
                </button>
                {(activeSection === section.key || activeSection === null) && (
                  <div className={`${styles.sectionBody} fade-in`}>
                    {renderValue(section.key, value)}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
