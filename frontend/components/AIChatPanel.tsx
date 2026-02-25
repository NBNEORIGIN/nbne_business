'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { aiChat } from '@/lib/api'

interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  toolCalls?: Array<{ tool: string; args: Record<string, any> }>
  timestamp?: string
}

const WELCOME_MESSAGE: ChatMessage = {
  role: 'assistant',
  content: "Hi! I'm your AI assistant. I can help you manage your business — staff, bookings, clients, compliance, and more.\n\nTry saying things like:\n• \"Sam has called in sick today\"\n• \"Show me today's bookings\"\n• \"Who's off today?\"\n• \"Any overdue compliance items?\"\n• \"Add a new lead: Jane Smith, £500\"",
  timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
}

const QUICK_ACTIONS = [
  { label: "Today's overview", text: "Give me a quick overview of today" },
  { label: "Who's off?", text: "Who is off today?" },
  { label: "Today's bookings", text: "Show me today's bookings" },
  { label: "Compliance check", text: "Any overdue compliance items?" },
]

export default function AIChatPanel({ isOpen, onToggle }: { isOpen: boolean; onToggle: () => void }) {
  const router = useRouter()
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  async function handleSend(text?: string) {
    const msg = (text || input).trim()
    if (!msg || loading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: msg,
      timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      // Send conversation history (user + assistant messages only)
      const apiMessages = newMessages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({ role: m.role, content: m.content }))

      const res = await aiChat(apiMessages)

      if (res.error) {
        // apiFetch-level error (network, 401, 500, etc.)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ ${res.error}`,
          timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
        }])
      } else if (res.data?.reply) {
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: res.data.reply,
          toolCalls: res.data.tool_calls,
          timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
        }
        setMessages(prev => [...prev, assistantMessage])

        // Handle navigation
        if (res.data.navigate) {
          setTimeout(() => router.push(res.data!.navigate!), 500)
        }
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '⚠️ No response from assistant. Please try again.',
          timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
        }])
      }
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '⚠️ Something went wrong. Please try again.',
        timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
      }])
    }

    setLoading(false)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function clearChat() {
    setMessages([WELCOME_MESSAGE])
  }

  if (!isOpen) return null

  return (
    <div style={styles.overlay}>
      <div style={styles.panel}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.headerLeft}>
            <div style={styles.aiIcon}>✨</div>
            <div>
              <div style={styles.headerTitle}>AI Assistant</div>
              <div style={styles.headerSub}>Your business co-pilot</div>
            </div>
          </div>
          <div style={styles.headerActions}>
            <button onClick={clearChat} style={styles.headerBtn} title="Clear chat">🗑️</button>
            <button onClick={onToggle} style={styles.headerBtn} title="Close">✕</button>
          </div>
        </div>

        {/* Quick Actions */}
        {messages.length <= 1 && (
          <div style={styles.quickActions}>
            {QUICK_ACTIONS.map((qa, i) => (
              <button
                key={i}
                onClick={() => handleSend(qa.text)}
                style={styles.quickBtn}
              >
                {qa.label}
              </button>
            ))}
          </div>
        )}

        {/* Messages */}
        <div style={styles.messagesContainer}>
          {messages.map((msg, i) => (
            <div key={i} style={msg.role === 'user' ? styles.userRow : styles.assistantRow}>
              {msg.role === 'assistant' && <div style={styles.avatar}>✨</div>}
              <div style={msg.role === 'user' ? styles.userBubble : styles.assistantBubble}>
                <div style={styles.msgContent}>
                  {msg.content.split('\n').map((line, j) => (
                    <span key={j}>
                      {line.startsWith('•') ? (
                        <span style={styles.bulletLine}>{line}</span>
                      ) : (
                        line
                      )}
                      {j < msg.content.split('\n').length - 1 && <br />}
                    </span>
                  ))}
                </div>
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div style={styles.toolCallsBadge}>
                    {msg.toolCalls.map((tc, k) => (
                      <span key={k} style={styles.toolChip}>
                        ⚡ {tc.tool.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}
                {msg.timestamp && <div style={styles.timestamp}>{msg.timestamp}</div>}
              </div>
              {msg.role === 'user' && <div style={styles.userAvatar}>You</div>}
            </div>
          ))}
          {loading && (
            <div style={styles.assistantRow}>
              <div style={styles.avatar}>✨</div>
              <div style={styles.assistantBubble}>
                <div style={styles.typingDots}>
                  <span style={styles.dot}>●</span>
                  <span style={{ ...styles.dot, animationDelay: '0.2s' }}>●</span>
                  <span style={{ ...styles.dot, animationDelay: '0.4s' }}>●</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={styles.inputArea}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything about your business..."
            style={styles.textarea}
            rows={1}
            disabled={loading}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            style={{
              ...styles.sendBtn,
              opacity: loading || !input.trim() ? 0.4 : 1,
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '...' : '→'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Floating trigger button (used separately) ───

export function AIChatTrigger({ onClick, hasUnread }: { onClick: () => void; hasUnread?: boolean }) {
  return (
    <button onClick={onClick} style={styles.trigger} title="AI Assistant">
      <span style={{ fontSize: '1.5rem' }}>✨</span>
      {hasUnread && <span style={styles.unreadDot} />}
    </button>
  )
}


// ─── Styles ───

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    right: 0,
    bottom: 0,
    width: '420px',
    maxWidth: '100vw',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '-4px 0 24px rgba(0,0,0,0.15)',
  },
  panel: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    background: '#f8fafc',
    borderLeft: '1px solid #e2e8f0',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0.85rem 1rem',
    background: '#0f172a',
    color: '#fff',
    flexShrink: 0,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.65rem',
  },
  aiIcon: {
    fontSize: '1.5rem',
  },
  headerTitle: {
    fontWeight: 700,
    fontSize: '0.95rem',
  },
  headerSub: {
    fontSize: '0.7rem',
    opacity: 0.6,
  },
  headerActions: {
    display: 'flex',
    gap: '0.25rem',
  },
  headerBtn: {
    background: 'none',
    border: 'none',
    color: '#fff',
    fontSize: '1rem',
    cursor: 'pointer',
    padding: '0.35rem 0.5rem',
    borderRadius: '6px',
    opacity: 0.7,
    transition: 'opacity 0.15s',
  },
  quickActions: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '0.4rem',
    padding: '0.75rem 1rem',
    borderBottom: '1px solid #e2e8f0',
    background: '#fff',
    flexShrink: 0,
  },
  quickBtn: {
    padding: '0.35rem 0.75rem',
    borderRadius: '16px',
    border: '1px solid #e2e8f0',
    background: '#fff',
    fontSize: '0.75rem',
    fontWeight: 500,
    color: '#334155',
    cursor: 'pointer',
    transition: 'all 0.15s',
    fontFamily: 'inherit',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.85rem',
  },
  userRow: {
    display: 'flex',
    justifyContent: 'flex-end',
    alignItems: 'flex-end',
    gap: '0.5rem',
  },
  assistantRow: {
    display: 'flex',
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
    gap: '0.5rem',
  },
  avatar: {
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    background: '#0f172a',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.75rem',
    flexShrink: 0,
  },
  userAvatar: {
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    background: '#2563eb',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.55rem',
    fontWeight: 700,
    flexShrink: 0,
  },
  userBubble: {
    background: '#2563eb',
    color: '#fff',
    padding: '0.6rem 0.85rem',
    borderRadius: '14px 14px 4px 14px',
    maxWidth: '80%',
    fontSize: '0.85rem',
    lineHeight: 1.5,
  },
  assistantBubble: {
    background: '#fff',
    color: '#0f172a',
    padding: '0.6rem 0.85rem',
    borderRadius: '14px 14px 14px 4px',
    maxWidth: '85%',
    fontSize: '0.85rem',
    lineHeight: 1.5,
    border: '1px solid #e2e8f0',
  },
  msgContent: {
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
  },
  bulletLine: {
    display: 'block',
    paddingLeft: '0.25rem',
    fontSize: '0.82rem',
    color: '#475569',
  },
  toolCallsBadge: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '0.3rem',
    marginTop: '0.5rem',
    paddingTop: '0.4rem',
    borderTop: '1px solid #f1f5f9',
  },
  toolChip: {
    background: '#f0fdf4',
    color: '#166534',
    fontSize: '0.65rem',
    fontWeight: 600,
    padding: '0.15rem 0.5rem',
    borderRadius: '8px',
    border: '1px solid #bbf7d0',
  },
  timestamp: {
    fontSize: '0.6rem',
    color: '#94a3b8',
    marginTop: '0.3rem',
    textAlign: 'right' as const,
  },
  typingDots: {
    display: 'flex',
    gap: '0.25rem',
    padding: '0.2rem 0',
  },
  dot: {
    fontSize: '0.7rem',
    color: '#94a3b8',
    animation: 'pulse 1s ease-in-out infinite',
  },
  inputArea: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '0.5rem',
    padding: '0.75rem 1rem',
    borderTop: '1px solid #e2e8f0',
    background: '#fff',
    flexShrink: 0,
  },
  textarea: {
    flex: 1,
    padding: '0.6rem 0.85rem',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    fontSize: '0.85rem',
    fontFamily: 'inherit',
    resize: 'none' as const,
    outline: 'none',
    maxHeight: '120px',
    lineHeight: 1.4,
    background: '#f8fafc',
  },
  sendBtn: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    border: 'none',
    background: '#2563eb',
    color: '#fff',
    fontSize: '1.1rem',
    fontWeight: 700,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    transition: 'opacity 0.15s',
    fontFamily: 'inherit',
  },
  trigger: {
    position: 'fixed' as const,
    bottom: '5rem',
    right: '1.5rem',
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    background: '#0f172a',
    border: 'none',
    boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 999,
    transition: 'transform 0.15s, box-shadow 0.15s',
  },
  unreadDot: {
    position: 'absolute' as const,
    top: '4px',
    right: '4px',
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    background: '#ef4444',
    border: '2px solid #0f172a',
  },
}
