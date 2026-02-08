'use client'

import { useState, useRef, useEffect } from 'react'
import { DEMO_CHANNELS, DEMO_MESSAGES } from '@/lib/demo-data'
import type { Channel, ChatMessage } from '@/lib/types'

const CURRENT_USER_ID = 'u1'
const CURRENT_USER_NAME = 'Jordan Riley'

export default function AdminChatPage() {
  const [activeChannel, setActiveChannel] = useState<Channel>(DEMO_CHANNELS[0])
  const [allMessages, setAllMessages] = useState<Record<number, ChatMessage[]>>({ ...DEMO_MESSAGES })
  const [input, setInput] = useState('')
  const [typingUser, setTypingUser] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const messages = allMessages[activeChannel.id] || []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, activeChannel.id])

  function sendMessage(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim()) return
    const newMsg: ChatMessage = {
      id: Date.now(), channel_id: activeChannel.id, sender_name: CURRENT_USER_NAME,
      sender_id: CURRENT_USER_ID, body: input.trim(), message_type: 'text',
      created_at: new Date().toISOString(), read_by: [CURRENT_USER_ID], delivered: true,
    }
    setAllMessages(prev => ({ ...prev, [activeChannel.id]: [...(prev[activeChannel.id] || []), newMsg] }))
    setInput('')
    setTypingUser('Sam Kim')
    setTimeout(() => {
      setTypingUser(null)
      const reply: ChatMessage = {
        id: Date.now() + 1, channel_id: activeChannel.id, sender_name: 'Sam Kim',
        sender_id: 'u2', body: 'Got it, thanks! 👍', message_type: 'text',
        created_at: new Date().toISOString(), read_by: ['u2'], delivered: true,
      }
      setAllMessages(prev => ({ ...prev, [activeChannel.id]: [...(prev[activeChannel.id] || []), reply] }))
    }, 1500)
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div>
      <div className="page-header"><h1>Team Chat</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="chat-layout">
        <div className="chat-channels">
          <h3>Channels</h3>
          {DEMO_CHANNELS.map(ch => (
            <div key={ch.id} className={`channel-item ${activeChannel.id === ch.id ? 'active' : ''}`} onClick={() => { setActiveChannel(ch); setTypingUser(null) }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="ch-name">{ch.channel_type === 'DIRECT' ? '👤' : '#'} {ch.name}</span>
                {ch.unread_count > 0 && <span className="ch-unread">{ch.unread_count}</span>}
              </div>
              <div className="ch-meta">{ch.member_count} members</div>
            </div>
          ))}
        </div>
        <div className="chat-messages">
          <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)', fontWeight: 600 }}>
            {activeChannel.channel_type === 'DIRECT' ? '👤' : '#'} {activeChannel.name}
          </div>
          <div className="messages-list">
            {messages.map(msg => {
              const isYou = msg.sender_id === CURRENT_USER_ID
              return (
                <div key={msg.id} className={`msg ${isYou ? 'msg-you' : ''}`}>
                  {!isYou && <div className="msg-sender">{msg.sender_name}</div>}
                  <div className="msg-body">{msg.body}</div>
                  <div className="msg-time">{formatTime(msg.created_at)}</div>
                </div>
              )
            })}
            {typingUser && <div className="typing-indicator">{typingUser} is typing...</div>}
            <div ref={messagesEndRef} />
          </div>
          <form className="chat-input-bar" onSubmit={sendMessage}>
            <input value={input} onChange={e => setInput(e.target.value)} placeholder={`Message #${activeChannel.name}...`} autoFocus />
            <button type="submit" className="btn btn-primary btn-sm">Send</button>
          </form>
        </div>
      </div>
    </div>
  )
}
