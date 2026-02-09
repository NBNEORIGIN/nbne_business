'use client'

import { useState, useRef, useEffect } from 'react'
import { getChannels, getMessages, sendMessage as apiSendMessage, getCurrentUser, getMediaUrl, isImageFile, isVideoFile } from '@/lib/api'

export default function AdminChatPage() {
  const [channels, setChannels] = useState<any[]>([])
  const [activeChannel, setActiveChannel] = useState<any | null>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
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

  // Poll for new messages every 5 seconds
  useEffect(() => {
    if (!activeChannel) return
    const interval = setInterval(() => {
      getMessages(activeChannel.id).then(r => { if (r.data) setMessages(r.data) })
    }, 5000)
    return () => clearInterval(interval)
  }, [activeChannel?.id])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if ((!input.trim() && files.length === 0) || !activeChannel) return
    setSending(true)
    const res = await apiSendMessage(activeChannel.id, input.trim(), files.length > 0 ? files : undefined)
    if (res.data) {
      setMessages(prev => [...prev, res.data])
    }
    setInput('')
    setFiles([])
    if (fileInputRef.current) fileInputRef.current.value = ''
    setSending(false)
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) setFiles(Array.from(e.target.files))
  }

  function removeFile(idx: number) {
    setFiles(prev => prev.filter((_, i) => i !== idx))
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }

  function renderAttachments(attachments: any[]) {
    if (!attachments || attachments.length === 0) return null
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
        {attachments.map((att: any) => {
          const url = getMediaUrl(att.url)
          const isImage = att.content_type?.startsWith('image/') || isImageFile(att.filename || '')
          const isVideo = att.content_type?.startsWith('video/') || isVideoFile(att.filename || '')
          if (isImage) {
            return <a key={att.id} href={url} target="_blank" rel="noopener"><img src={url} alt={att.filename} style={{ maxWidth: 240, maxHeight: 180, borderRadius: 'var(--radius)', objectFit: 'cover' }} /></a>
          }
          if (isVideo) {
            return <video key={att.id} src={url} controls style={{ maxWidth: 300, maxHeight: 200, borderRadius: 'var(--radius)' }} />
          }
          return <a key={att.id} href={url} target="_blank" rel="noopener" style={{ fontSize: '0.85rem', color: 'var(--color-primary)' }}>📎 {att.filename}</a>
        })}
      </div>
    )
  }

  if (loading) return <div className="empty-state">Loading chat…</div>

  return (
    <div>
      <div className="page-header"><h1>Team Chat</h1><span className="badge badge-danger">Tier 3</span></div>
      <div className="chat-layout">
        <div className="chat-channels">
          <h3>Channels</h3>
          {channels.map((ch: any) => (
            <div key={ch.id} className={`channel-item ${activeChannel?.id === ch.id ? 'active' : ''}`} onClick={() => setActiveChannel(ch)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="ch-name">{ch.channel_type === 'DIRECT' ? '👤' : ch.channel_type === 'TEAM' ? '👥' : '#'} {ch.name}</span>
              </div>
              <div className="ch-meta">{ch.member_count} members</div>
            </div>
          ))}
        </div>
        <div className="chat-messages">
          <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)', fontWeight: 600 }}>
            {activeChannel ? (
              <>{activeChannel.channel_type === 'DIRECT' ? '👤' : '#'} {activeChannel.name}<span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginLeft: '0.5rem' }}>{activeChannel.member_count} members</span></>
            ) : 'Select a channel'}
          </div>
          <div className="messages-list">
            {messages.map((msg: any) => {
              const isYou = msg.sender_id === currentUserId
              return (
                <div key={msg.id} className={`msg ${isYou ? 'msg-you' : ''}`}>
                  {!isYou && <div className="msg-sender">{msg.sender_name}</div>}
                  {msg.body && <div className="msg-body">{msg.body}</div>}
                  {renderAttachments(msg.attachments)}
                  <div className="msg-time">{formatTime(msg.created_at)}</div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* File preview bar */}
          {files.length > 0 && (
            <div style={{ padding: '0.5rem 1rem', borderTop: '1px solid var(--color-border)', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', background: 'var(--color-bg)' }}>
              {files.map((f, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: '4px 8px', fontSize: '0.8rem' }}>
                  {f.type.startsWith('image/') ? '🖼️' : f.type.startsWith('video/') ? '🎬' : '📎'} {f.name.length > 20 ? f.name.slice(0, 17) + '...' : f.name}
                  <button type="button" onClick={() => removeFile(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-danger)', fontWeight: 700, fontSize: '1rem', lineHeight: 1 }}>×</button>
                </div>
              ))}
            </div>
          )}

          <form className="chat-input-bar" onSubmit={handleSend}>
            <input type="file" ref={fileInputRef} onChange={handleFileSelect} multiple accept="image/*,video/*,.pdf,.doc,.docx" style={{ display: 'none' }} />
            <button type="button" onClick={() => fileInputRef.current?.click()} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.3rem', padding: '0 0.5rem' }} title="Attach files">📎</button>
            <input value={input} onChange={e => setInput(e.target.value)} placeholder={activeChannel ? `Message #${activeChannel.name}...` : 'Select a channel'} autoFocus disabled={!activeChannel} style={{ flex: 1 }} />
            <button type="submit" className="btn btn-primary btn-sm" disabled={!activeChannel || sending}>{sending ? '...' : 'Send'}</button>
          </form>
        </div>
      </div>
    </div>
  )
}
