import React, { ReactNode } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { Moon, Sun } from 'lucide-react'
import crossroadsLogo from '../assets/crossroads-logo.png'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="header-content">
          <div className="logo-section">
            <img src={crossroadsLogo} alt="Crossroads Professional Services" className="logo-image" />
            <div className="logo-text">
              <h1 className="logo">
                <span className="logo-brown">CROSSROADS</span>
                <span className="logo-blue"> Professional Services</span>
              </h1>
              <p className="subtitle">Universal Recruiting Tool</p>
            </div>
          </div>
          <div className="header-actions">
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>
            {user && (
              <div className="user-menu">
                <span className="user-email">{user.email}</span>
                <button className="logout-btn" onClick={logout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>
      <div className="layout-body">
        <aside className="sidebar">
          <nav className="sidebar-nav">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `nav-link ${isActive || location.pathname === '/' ? 'active' : ''}`
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              History
            </NavLink>
            <NavLink
              to="/vault"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              Vault
            </NavLink>
          </nav>
        </aside>
        <main className="main-content">{children}</main>
      </div>
    </div>
  )
}

export default Layout

