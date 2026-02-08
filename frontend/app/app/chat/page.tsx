'use client'

import { useState, useRef, useEffect } from 'react'
import { getChannels, getMessages, sendMessage as apiSendMessage, getCurrentUser } from '@/lib/api'

export default function ChatPage() {
  const [channels, setChannels] = useState<any[]>([])
  const [activeChannel, setActiveChannel] = useState<any | null>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState('')
  const [typingUser, setTypingUser] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const currentUser = getCurrentUser()
  const currentUserId = currentUser?.id

  useEffect(() => {
    getChannels().then(r => {
      const chs = r.data || []
      setChannels(chs)
      if (chs.length > 0) setActiveChannel(chs[0])
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    if (!activeChannel) return
    getMessages(activeChannel.id).then(r => setMessages(r.data || []))
  }, [activeChannel?.id])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || !activeChannel) return
    const body = input.trim()
    setInput('')

    const res = await apiSendMessage(activeChannel.id, body)
    if (res.data) {
      setMessages(prev => [...prev, res.data])
    }

    // Simulate typing response for demo
    setTypingUser('Sam Kim')
    setTimeout(() => {
      setTypingUser(null)
    }, 1500 + Math.random() * 1000)
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }

  if (loading) return <div className="empty-state">Loading chat…</div>

  return (
    <div>
      <div className="page-header">
        <h1>Team Chat</h1>
        <span className="badge badge-success">Tier 2</span>
      </div>

      <div className="chat-layout">
        <div className="chat-channels">
          <h3>Channels</h3>
          {channels.map((ch: any) => (
            <div
              key={ch.id}
              className={`channel-item ${activeChannel?.id === ch.id ? 'active' : ''}`}
              onClick={() => { setActiveChannel(ch); setTypingUser(null) }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="ch-name">
                  {ch.channel_type === 'DIRECT' ? '👤' : ch.channel_type === 'TEAM' ? '👥' : '#'} {ch.name}
                </span>
              </div>
              <div className="ch-meta">{ch.member_count} members</div>
            </div>
          ))}
        </div>

        <div className="chat-messages">
          <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)', fontWeight: 600 }}>
            {activeChannel ? (
              <>
                {activeChannel.channel_type === 'DIRECT' ? '👤' : '#'} {activeChannel.name}
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginLeft: '0.5rem' }}>
                  {activeChannel.member_count} members
                </span>
              </>
            ) : 'Select a channel'}
          </div>

          <div className="messages-list">
            {messages.map((msg: any) => {
              const isYou = msg.sender_id === currentUserId
              return (
                <div key={msg.id} className={`msg ${isYou ? 'msg-you' : ''}`}>
                  {!isYou && <div className="msg-sender">{msg.sender_name}</div>}
                  <div className="msg-body">{msg.body}</div>
                  <div className="msg-time">{formatTime(msg.created_at)}</div>
                </div>
              )
            })}
            {typingUser && (
              <div className="typing-indicator">{typingUser} is typing...</div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-input-bar" onSubmit={handleSend}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={activeChannel ? `Message #${activeChannel.name}...` : 'Select a channel'}
              autoFocus
              disabled={!activeChannel}
            />
            <button type="submit" className="btn btn-primary btn-sm" disabled={!activeChannel}>Send</button>
          </form>
        </div>
      </div>
    </div>
  )
}
