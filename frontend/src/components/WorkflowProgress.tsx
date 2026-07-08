import { CheckCircle2, Circle, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import styles from './WorkflowProgress.module.css'

export interface WorkflowStep {
  id: string
  label: string
  description: string
  status: 'pending' | 'running' | 'done' | 'error' | 'retry'
}

const WORKFLOW_STEPS: Omit<WorkflowStep, 'status'>[] = [
  { id: 'planner', label: 'Planner', description: 'Building research strategy' },
  { id: 'researcher', label: 'Researcher', description: 'Searching the web' },
  { id: 'analyzer', label: 'Analyzer', description: 'Analyzing data' },
  { id: 'quality_check', label: 'Quality Check', description: 'Evaluating completeness' },
  { id: 'report_gen', label: 'Report Generation', description: 'Writing final briefing' },
]

interface Props {
  currentNode: string
  sessionStatus: string
  retryCount?: number
  qualityScore?: number
}

export default function WorkflowProgress({ currentNode, sessionStatus, retryCount = 0, qualityScore = 0 }: Props) {
  const getStepStatus = (stepId: string): WorkflowStep['status'] => {
    if (sessionStatus === 'failed') {
      if (stepId === currentNode) return 'error'
    }

    const order = ['planner', 'researcher', 'analyzer', 'quality_check', 'report_gen']
    const currentIdx = order.indexOf(currentNode)
    const stepIdx = order.indexOf(stepId)

    if (currentNode === 'increment_retry' && stepId === 'researcher') return 'retry'

    if (sessionStatus === 'completed') return 'done'
    if (currentIdx === -1) return 'pending'

    if (stepIdx < currentIdx) return 'done'
    if (stepIdx === currentIdx) {
      return sessionStatus === 'failed' ? 'error' : 'running'
    }
    return 'pending'
  }

  const steps: WorkflowStep[] = WORKFLOW_STEPS.map(s => ({
    ...s,
    status: getStepStatus(s.id),
  }))

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Research Workflow</h3>
        {retryCount > 0 && (
          <span className={styles.retryBadge}>
            <RefreshCw size={11} /> Retry #{retryCount}
          </span>
        )}
        {sessionStatus === 'completed' && qualityScore > 0 && (
          <span className={styles.scoreBadge}>
            Quality: {Math.round(qualityScore * 100)}%
          </span>
        )}
      </div>

      <div className={styles.steps}>
        {steps.map((step, idx) => (
          <div key={step.id} className={styles.stepRow}>
            {/* Connector line */}
            {idx > 0 && (
              <div className={`${styles.connector} ${steps[idx - 1].status === 'done' ? styles.connectorDone : ''}`} />
            )}

            <div className={`${styles.step} ${styles[`step-${step.status}`]}`}>
              <div className={styles.stepIcon}>
                {step.status === 'done' && <CheckCircle2 size={18} />}
                {step.status === 'running' && <Loader2 size={18} className={styles.spinIcon} />}
                {step.status === 'error' && <AlertCircle size={18} />}
                {step.status === 'retry' && <RefreshCw size={18} className={styles.spinIcon} />}
                {step.status === 'pending' && <Circle size={18} />}
              </div>
              <div className={styles.stepContent}>
                <span className={styles.stepLabel}>{step.label}</span>
                <span className={styles.stepDesc}>{step.description}</span>
              </div>
              {step.status === 'running' && (
                <div className={styles.runningDot} />
              )}
            </div>
          </div>
        ))}
      </div>

      {sessionStatus === 'running' && (
        <div className={styles.progressBar}>
          <div className={styles.progressFill} />
        </div>
      )}
    </div>
  )
}
