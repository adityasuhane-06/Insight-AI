import { Link, Outlet, useLocation } from 'react-router-dom'
import { Zap, Plus, Home } from 'lucide-react'
import styles from './Layout.module.css'

export default function Layout() {
  const location = useLocation()

  return (
    <div className={styles.root}>
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className={styles.header}>
        <div className={`container ${styles.headerInner}`}>
          <Link to="/" className={styles.logo}>
            <div className={styles.logoIcon}>
              <Zap size={18} />
            </div>
            <span>ZyLabs</span>
            <span className={styles.logoBadge}>Copilot</span>
          </Link>

          <nav className={styles.nav}>
            <Link
              to="/"
              className={`${styles.navLink} ${location.pathname === '/' ? styles.navLinkActive : ''}`}
            >
              <Home size={15} />
              Sessions
            </Link>
            <Link
              to="/new"
              className={`btn btn-primary btn-sm ${styles.newBtn}`}
              id="new-session-btn"
            >
              <Plus size={15} />
              New Research
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Main content ────────────────────────────────────────── */}
      <main className={styles.main}>
        <Outlet />
      </main>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className={styles.footer}>
        <div className="container">
          <p>ZyLabs AI Research Copilot · Built with LangGraph + FastAPI + React</p>
        </div>
      </footer>
    </div>
  )
}
