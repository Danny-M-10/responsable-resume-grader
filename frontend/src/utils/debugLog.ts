/**
 * Debug logging utility that works in both local development and AWS production
 * - Local: Sends logs to debug server endpoint
 * - Production: Logs to console (can be captured by CloudWatch if configured) 
 *   and optionally sends critical errors to backend API
 */

interface LogEntry {
  location: string
  message: string
  data?: any
  timestamp: number
  sessionId: string
  runId: string
  hypothesisId?: string
}

const DEBUG_ENDPOINT = 'http://127.0.0.1:7243/ingest/d2b8802d-14c8-4b33-b4a5-574dd9e6d4f5'
const isProduction = import.meta.env.PROD
const isLocalDebug = !isProduction && typeof window !== 'undefined'

/**
 * Log debug information
 */
export function debugLog(entry: LogEntry): void {
  const { location, message, data, timestamp: _timestamp, sessionId: _sessionId, runId: _runId, hypothesisId } = entry
  
  // Always log to console in production for CloudWatch visibility
  const logLevel = message.toLowerCase().includes('error') ? 'error' : 'info'
  const consolePrefix = hypothesisId ? `[HYP-${hypothesisId}]` : '[DEBUG]'
  const logMessage = `${consolePrefix} ${location}: ${message}`
  
  if (logLevel === 'error') {
    console.error(logMessage, data || {})
  } else {
    console.log(logMessage, data || {})
  }
  
  // In local development, also send to debug endpoint
  if (isLocalDebug) {
    try {
      fetch(DEBUG_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
        // Don't wait for response - fire and forget
      }).catch(() => {
        // Silently fail if debug endpoint is not available
      })
    } catch (err) {
      // Ignore errors
    }
  }
  
  // In production, optionally send critical errors to backend for CloudWatch logging
  // This would require a backend endpoint - commented out for now
  // if (isProduction && logLevel === 'error') {
  //   try {
  //     apiClient.post('/api/debug/log', entry).catch(() => {})
  //   } catch (err) {
  //     // Ignore errors
  //   }
  // }
}
