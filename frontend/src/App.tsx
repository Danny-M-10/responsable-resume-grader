import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ToastProvider } from './contexts/ToastContext'
import Layout from './components/Layout'
import ToastContainer from './components/Toast'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Results from './pages/Results'
import History from './pages/History'
import VaultPage from './pages/VaultPage'
import ProtectedRoute from './components/ProtectedRoute'
import { debugLog } from './utils/debugLog'

function App() {
  // #region agent log - Global error handler
  React.useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      debugLog({location:'App.tsx:global-error-handler',message:'Global error caught',data:{errorMessage:event.message,errorFilename:event.filename,errorLineno:event.lineno,errorColno:event.colno,errorStack:event.error?.stack?.substring(0,300)},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'D'});
    }
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      debugLog({location:'App.tsx:global-unhandled-rejection',message:'Unhandled promise rejection',data:{reason:event.reason?.toString?.()?.substring(0,200),errorStack:event.reason?.stack?.substring(0,300)},timestamp:Date.now(),sessionId:'debug-session',runId:'initial',hypothesisId:'D'});
    }
    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleUnhandledRejection)
    return () => {
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    }
  }, [])
  // #endregion
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <Router>
            <ToastContainer />
            <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/results/:analysisId"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Results />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <Layout>
                    <History />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/vault"
              element={
                <ProtectedRoute>
                  <Layout>
                    <VaultPage />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}

export default App

