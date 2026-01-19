import React, { useState, useRef, useEffect } from 'react'
import { Send, MessageCircle, X, Loader2, AlertCircle } from 'lucide-react'
import { chatService } from '../services/chatService'
import './AnalysisChat.css'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface AnalysisChatProps {
  analysisId: string
  jobDetails?: {
    title?: string
    location?: string
  }
}

const AnalysisChat: React.FC<AnalysisChatProps> = ({
  analysisId,
  jobDetails,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [error, setError] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input when chat is expanded
  useEffect(() => {
    if (expanded && inputRef.current) {
      inputRef.current.focus()
    }
  }, [expanded])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const response = await chatService.sendMessage(analysisId, userMessage.content)
      
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get response'
      setError(errorMessage)
      
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I'm sorry, I encountered an error: ${errorMessage}. Please try again.`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const jobTitle = jobDetails?.title || 'this analysis'

  return (
    <div className={`analysis-chat ${expanded ? 'expanded' : ''}`}>
      {/* Chat Toggle Button */}
      <button
        className="chat-toggle-btn"
        onClick={() => setExpanded(!expanded)}
        aria-label={expanded ? 'Close chat' : 'Open chat'}
        aria-expanded={expanded}
      >
        <MessageCircle size={24} aria-hidden="true" />
        {expanded && <X size={20} className="close-icon" aria-hidden="true" />}
      </button>

      {/* Chat Panel */}
      {expanded && (
        <div className="chat-panel">
          {/* Chat Header */}
          <div className="chat-header">
            <div className="chat-header-content">
              <MessageCircle size={20} aria-hidden="true" />
              <div>
                <h3>Ask About Candidate Selection</h3>
                <p className="chat-subtitle">
                  Chatting about analysis for {jobTitle}
                </p>
              </div>
            </div>
            <button
              className="chat-close-btn"
              onClick={() => setExpanded(false)}
              aria-label="Close chat"
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="chat-empty-state">
                <MessageCircle size={48} className="empty-icon" aria-hidden="true" />
                <h4>Start a conversation</h4>
                <p>Ask questions about candidate selection, rankings, or scoring rationale.</p>
                <div className="example-questions">
                  <p className="example-label">Example questions:</p>
                  <ul>
                    <li>Why was [Candidate Name] ranked #1?</li>
                    <li>What are the differences between the top 3 candidates?</li>
                    <li>Explain the scoring rationale for a specific candidate</li>
                  </ul>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`chat-message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
                  >
                    <div className="message-content">{message.content}</div>
                    <div className="message-timestamp">
                      {message.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="chat-message assistant-message loading">
                    <div className="message-content">
                      <Loader2 className="spinner" size={16} aria-hidden="true" />
                      <span>Thinking...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="chat-error" role="alert">
              <AlertCircle size={16} aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* Input Area */}
          <div className="chat-input-area">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Ask about candidate selection..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={2}
              disabled={loading}
              aria-label="Chat input"
            />
            <button
              className="chat-send-btn"
              onClick={handleSend}
              disabled={!input.trim() || loading}
              aria-label="Send message"
            >
              {loading ? (
                <Loader2 className="spinner" size={18} aria-hidden="true" />
              ) : (
                <Send size={18} aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalysisChat
