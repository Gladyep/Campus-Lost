import { useEffect, useMemo, useState } from 'react'
import { createClaim, decideClaim } from './api/claims.js'
import { login, register } from './api/auth.js'
import { getItems, createItem } from './api/items.js'
import { getResource, getResourceCount, markNotificationRead, decideReport } from './api/resources.js'
import VisualSearch from './VisualSearch.jsx'
import { request } from './api/client.js'
import './Campus.css'

const sampleItems = [
  { id: 'demo-1', title: 'Silver laptop, small sticker on lid', category_name: 'Electronics', item_type: 'FOUND', location: 'North Library, 2nd floor', event_date: '2026-10-10', description: 'Found near the quiet study desks. A small blue planet sticker is on the lid.', image_url: 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=85', status: 'FOUND' },
  { id: 'demo-2', title: 'Canvas tote with sketchbooks', category_name: 'Bags', item_type: 'LOST', location: 'Arts building', event_date: '2026-10-11', description: 'Natural canvas tote with two sketchbooks and a green pencil case.', image_url: 'https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=900&q=85', status: 'LOST' },
  { id: 'demo-3', title: 'Set of keys on a red carabiner', category_name: 'Keys', item_type: 'FOUND', location: 'West residence hall', event_date: '2026-10-09', description: 'Three keys and a small round keychain. Left with the residence desk.', image_url: 'https://images.unsplash.com/photo-1582139329536-e7284fece509?auto=format&fit=crop&w=900&q=85', status: 'FOUND' },
  { id: 'demo-4', title: 'Black over-ear headphones', category_name: 'Electronics', item_type: 'LOST', location: 'Student union', event_date: '2026-10-08', description: 'Black headphones, soft padded case may be nearby.', image_url: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85', status: 'LOST' },
  { id: 'demo-5', title: 'Stainless steel water bottle', category_name: 'Accessories', item_type: 'FOUND', location: 'Gymnasium court 1', event_date: '2026-10-07', description: 'Matte green bottle with a few small white decals.', image_url: 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=85', status: 'FOUND' },
  { id: 'demo-6', title: 'Navy backpack with key clip', category_name: 'Bags', item_type: 'LOST', location: 'Engineering courtyard', event_date: '2026-10-06', description: 'Navy daypack with a silver clip inside the front pocket.', image_url: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85', status: 'LOST' },
]

const navigation = ['Discover', 'My reports', 'Matches', 'Visual Search', 'Messages', 'Alerts']
const categories = ['Electronics', 'Bags', 'Keys', 'Accessories', 'Books', 'Clothing', 'Other']
const today = new Date().toISOString().slice(0, 10)

function itemImage(item) {
  const image = item.images?.[0]?.image || item.image_url || ''
  if (image.startsWith('/')) {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
    return `${apiUrl.replace(/\/api\/?$/, '')}${image}`
  }
  return image
}

function dateLabel(date) {
  if (!date) return 'Date not listed'
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(new Date(`${date}T12:00:00`))
}

function App() {
  const [view, setView] = useState('Discover')
  const [items, setItems] = useState(sampleItems)
  const [resourceRows, setResourceRows] = useState([])
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [categoryFilter, setCategoryFilter] = useState('All categories')
  const [auth, setAuth] = useState(null)
  const [authOpen, setAuthOpen] = useState(false)
  const [reportOpen, setReportOpen] = useState(false)
  const [authError, setAuthError] = useState('')
  const [notice, setNotice] = useState('')
  const [backendOnline, setBackendOnline] = useState(false)
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState(null)
  const [reportType, setReportType] = useState('LOST')
  const navItems = auth?.user?.role === 'ADMIN' ? [...navigation, 'Admin dashboard'] : navigation

  useEffect(() => {
    const token = auth?.access
    if (!token) return undefined

    let active = true
    const params = new URLSearchParams()
    params.set('mine', 'true')
    Promise.allSettled([
      getItems(params, token),
      getResourceCount('matches/', token),
    ]).then(([reportsResult, matchesResult]) => {
      if (!active) return
      setSummary({
        token,
        reports: reportsResult.status === 'fulfilled' ? reportsResult.value.count : null,
        matches: matchesResult.status === 'fulfilled' ? matchesResult.value : null,
      })
    })

    return () => { active = false }
  }, [auth?.access])

  useEffect(() => {
    if (view === 'Visual Search') return undefined

    let active = true
    const load = async () => {
      if (view === 'My reports' && !auth?.access) {
        setItems([])
        setBackendOnline(false)
        setLoading(false)
        return
      }
      setLoading(true)
      try {
        if (view === 'Discover' || view === 'My reports') {
          const params = new URLSearchParams()
          if (search) params.set('search', search)
                  if (view === 'Discover') {
                    if (typeFilter === 'RECOVERED') params.set('status', 'RECOVERED')
                    else if (typeFilter !== 'ALL') params.set('item_type', typeFilter)
                  }
                  if (categoryFilter !== 'All categories' && view === 'Discover') params.set('category_name', categoryFilter)
                  if (view === 'My reports') params.set('mine', 'true')
                  const result = await getItems(params, auth?.access)
                  if (active) {
                    setItems(result.rows)
                    setBackendOnline(true)
                  }
                } else {
          const endpoints = { Matches: 'matches/', Messages: 'conversations/', Alerts: 'notifications/', 'Admin dashboard': 'admin/dashboard/' }
          const result = await getResource(endpoints[view], auth?.access)
          if (active) {
            if (view === 'Admin dashboard') {
              const flagged = await getResource('admin/flagged-claims/', auth?.access)
              setResourceRows([
                { id: 'open-items', title: 'Open reports', status: result.open_items },
                { id: 'pending-claims', title: 'Claims needing review', status: result.pending_claims },
                { id: 'pending-reports', title: 'Reports awaiting moderation', status: result.pending_reports },
                ...(result.recent_reports || []).map((item) => ({ ...item, kind: 'report', title: item['item__title'] || 'User report', description: item.reason, status: 'PENDING' })),
                ...flagged.map((claim) => ({ ...claim, kind: 'claim', title: claim.item_title, description: `Flagged claim from ${claim.claimant_name}`, status: claim.status })),
              ])
            } else {
              setResourceRows(result)
            }
            setBackendOnline(true)
          }
        }
      } catch {
        if (active) {
          setBackendOnline(false)
          if (view === 'Discover') setItems(sampleItems)
          else setResourceRows([])
        }
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [view, search, typeFilter, categoryFilter, auth?.access])

  useEffect(() => {
    if (!notice) return undefined
    const timeoutId = window.setTimeout(() => setNotice(''), 4500)
    return () => window.clearTimeout(timeoutId)
  }, [notice])

  const visibleItems = useMemo(() => {
    if (backendOnline) return items
    const needle = search.trim().toLowerCase()
    return items.filter((item) => {
      const text = `${item.title} ${item.description} ${item.location} ${item.category_name}`.toLowerCase()
      return (!needle || text.includes(needle)) && (typeFilter === 'ALL' || item.item_type === typeFilter) && (categoryFilter === 'All categories' || item.category_name === categoryFilter)
    })
  }, [items, backendOnline, search, typeFilter, categoryFilter])

  async function submitAuth(event) {
    event.preventDefault()
    setAuthError('')
    const form = new FormData(event.currentTarget)
    try {
      const result = form.get('mode') === 'register'
        ? await register({ name: form.get('name'), email: form.get('email'), password: form.get('password') })
        : await login({ email: form.get('email'), password: form.get('password') })
      setAuth({ access: result.access, user: result.user || { name: form.get('name') || form.get('email'), role: 'USER' } })
      setAuthOpen(false)
      setNotice('You are signed in. Welcome to CampusConnect.')
    } catch (error) {
      setAuthError(error.message)
    }
  }

  async function submitReport(event) {
    event.preventDefault()
    if (!auth?.access) {
      setReportOpen(false)
      setAuthOpen(true)
      setNotice('Sign in to publish a report.')
      return
    }
    const form = new FormData(event.currentTarget)
    try {
      await createItem(form, auth.access)
      setReportOpen(false)
      setView('My reports')
      setNotice('Your report is live. We will look for possible matches.')
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function claimItem(item) {
    if (!auth?.access) {
      setAuthOpen(true)
      setNotice('Sign in to start an ownership claim.')
      return
    }
    const evidence = window.prompt('Share a detail that can help verify this item:')
    if (!evidence?.trim()) return
    try {
      await createClaim({ item: item.id, evidence }, auth.access)
      setNotice('Claim submitted. The finder will review it privately.')
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function contactReporter(item) {
    if (!auth?.access) {
      setAuthOpen(true)
      setNotice('Sign in to contact the reporter.')
      return
    }
    try {
      await request('conversations/', { method: 'POST', body: JSON.stringify({ item: item.id }), token: auth.access })
      setView('Messages')
      setNotice('Conversation started. Check Messages for replies.')
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function markRecovered(item) {
    if (!auth?.access) {
      setAuthOpen(true)
      setNotice('Sign in to manage your report.')
      return
    }
    const ok = window.confirm('Confirm marking this report as recovered. This will archive it from active lists.')
    if (!ok) return
    try {
      const updated = await request(`items/${item.id}/recover/`, { method: 'POST', token: auth.access })
      setItems((rows) => rows.map((r) => (r.id === updated.id ? updated : r)))
      setNotice('Report marked as recovered.')
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function markAlertRead(id) {
    try {
      await markNotificationRead(id, auth?.access)
      setResourceRows((rows) => rows.map((row) => row.id === id ? { ...row, is_read: true } : row))
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function decideModeration(row, decision) {
    const reason = window.prompt('Add a short decision note:')
    if (reason === null) return
    try {
      if (row.kind === 'claim') await decideClaim(row.id, decision, reason, auth?.access)
      else await decideReport(row.id, decision, reason, auth?.access)
      setResourceRows((rows) => rows.filter((entry) => !(entry.id === row.id && entry.kind === row.kind)))
      setNotice('Moderation decision recorded.')
    } catch (error) {
      setNotice(error.message)
    }
  }

  const pageTitle = view === 'Discover' ? 'Recently reported' : view
  const fullName = typeof auth?.user?.name === 'string' ? auth.user.name.trim() : ''
  const firstName = fullName.split(/\s+/)[0]

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#discover" onClick={() => setView('Discover')} aria-label="CampusConnect home">
          <span className="brand-mark">cc</span><span>campus<span className="brand-light">connect</span></span>
        </a>
        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map((label, index) => <button key={label} className={view === label ? 'nav-link active' : 'nav-link'} onClick={() => setView(label)}><span className="nav-icon" aria-hidden="true">{['⌂', '▤', '⌕', '▧', '✉', '◉', '◆'][index]}</span>{label}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <p className="sidebar-note">Helping our campus find its way back.</p>
          <div className="account-area">
            {auth ? <><span className="user-name">{auth.user?.name || auth.user?.email}</span><button className="text-button" onClick={() => { setAuth(null); setView('Discover') }}>Sign out</button></> : <button className="sign-in" onClick={() => setAuthOpen(true)}>Sign in <span aria-hidden="true">↗</span></button>}
          </div>
        </div>
      </header>

      <div className="main-area">
        <section className="dashboard-header">
          <div>
            <p className="dashboard-greeting">{firstName ? <>Hey, {firstName}! <span aria-hidden="true">👋</span></> : 'Welcome to CampusConnect'}</p>
            <p className="dashboard-subtitle">Here’s what’s happening in your campus community.</p>
          </div>
          <button className="report-button header-report" onClick={() => { setReportType('LOST'); setReportOpen(true) }}><span aria-hidden="true">＋</span> Report an item</button>
        </section>

        {view === 'Discover' && <>
          <section className="summary-grid" aria-label="Your campus summary">
            <article className="summary-card report-summary">
              <span className="summary-icon" aria-hidden="true">▤</span>
              <div><p>My reports</p><strong>{summary && summary.token === auth?.access ? summary.reports ?? '—' : '—'}</strong><span>{auth ? 'Reports submitted by you' : 'Sign in to view your count'}</span></div>
            </article>
            <article className="summary-card match-summary">
              <span className="summary-icon" aria-hidden="true">⌕</span>
              <div><p>Potential matches</p><strong>{summary && summary.token === auth?.access ? summary.matches ?? '—' : '—'}</strong><span>{auth ? 'Possible item connections' : 'Sign in to view your matches'}</span></div>
            </article>
          </section>
          <section className="quick-actions" aria-label="Quick actions">
            <div className="quick-actions-heading"><p className="eyebrow muted">PICK UP WHERE YOU NEED</p><h2>Quick actions</h2></div>
            <button className="quick-action quick-lost" onClick={() => { setReportType('LOST'); setReportOpen(true) }}><span className="quick-action-mark" aria-hidden="true">−</span><span>Report a lost item</span><span className="quick-arrow" aria-hidden="true">↗</span></button>
            <button className="quick-action quick-found" onClick={() => { setReportType('FOUND'); setReportOpen(true) }}><span className="quick-action-mark" aria-hidden="true">＋</span><span>Report a found item</span><span className="quick-arrow" aria-hidden="true">↗</span></button>
            <button className="quick-action quick-browse" onClick={() => setView('Discover')}><span className="quick-action-mark" aria-hidden="true">⌕</span><span>Browse recent reports</span><span className="quick-arrow" aria-hidden="true">↗</span></button>
          </section>
        </>}

      <main className="content-wrap">
        <div className="context-row"><div><p className="eyebrow muted">{view === 'Discover' ? 'THE COMMUNITY BOARD' : 'YOUR CAMPUS SPACE'}</p><h2>{pageTitle}<span className="heading-period">.</span></h2></div><div className="context-meta"><span className={backendOnline ? 'connection-state online' : 'connection-state'}><i />{backendOnline ? 'Live campus feed' : 'Preview feed'}</span><span className="context-date">Updated just now</span></div></div>

        {view === 'Visual Search' ? <VisualSearch auth={auth} onSignIn={() => setAuthOpen(true)} onClaim={claimItem} /> : view === 'Discover' || (view === 'My reports' && auth) ? <>
          <div className="toolbar"><label className="search-box"><span aria-hidden="true">⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search an item, place, or detail" aria-label="Search reports" /><kbd>/</kbd></label><label className="category-select"><span className="sr-only">Filter by category</span><select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}><option>All categories</option>{categories.map((category) => <option key={category}>{category}</option>)}</select></label><button className="report-button" onClick={() => { setReportType('LOST'); setReportOpen(true) }}><span aria-hidden="true">＋</span> Report an item</button></div>
          <div className="filter-row"><div className="segmented" role="group" aria-label="Filter by report type">{[['ALL', 'Everything'], ['LOST', 'Lost'], ['FOUND', 'Found'], ['RECOVERED', 'Recovered']].map(([value, label]) => <button key={value} className={typeFilter === value ? 'segment selected' : 'segment'} onClick={() => setTypeFilter(value)}>{label}</button>)}</div><span className="result-count">{loading ? 'Updating…' : `${visibleItems.length} reports`}</span></div>
          {!backendOnline && view === 'Discover' && <p className="preview-note">Showing example listings while the Django API is offline.</p>}
          <section className="item-grid" aria-label="Item reports">
            {visibleItems.map((item, index) => <article className="item-card" key={item.id} style={{ '--card-delay': `${index * 55}ms` }}>
              <div className="item-image-wrap">{itemImage(item) ? <img className="item-image" src={itemImage(item)} alt={item.title} loading="lazy" /> : <div className={`image-placeholder tone-${index % 4}`} aria-hidden="true"><span>{(item.category_name || 'Campus').slice(0, 1)}</span></div>}<span className={`type-tag ${item.item_type === 'FOUND' ? 'found' : 'lost'}`}><i />{item.item_type === 'FOUND' ? 'Found' : 'Lost'}</span><span className="image-date">{dateLabel(item.event_date)}</span></div>
              <div className="item-card-body"><div className="item-category">{item.category_name || item.category?.name || 'Campus item'}</div><h3>{item.title}</h3><p className="item-location"><span aria-hidden="true">⌖</span>{item.location}</p><p className="item-description">{item.description}</p><div className="item-card-footer"><span>{item.status === 'RETURNED' ? 'Reunited' : 'Campus report'}</span>{item.status === 'RECOVERED' && <span className="status-badge recovered">Recovered</span>}{item.item_type === 'FOUND' && <button className="claim-link" onClick={() => claimItem(item)}>That might be mine <span aria-hidden="true">↗</span></button>}{!(item.status === 'RECOVERED' || item.status === 'RETURNED' || item.status === 'CLOSED') && <button className="claim-link" onClick={() => contactReporter(item)}>Contact reporter <span aria-hidden="true">↗</span></button>}{item.is_reporter && item.status !== 'RECOVERED' && item.status !== 'RETURNED' && item.status !== 'CLOSED' && <button className="text-button" onClick={() => markRecovered(item)}>Mark recovered</button>}</div></div>
            </article>)}
          </section>
          {!visibleItems.length && <div className="empty-state"><span className="empty-mark">⌕</span><h3>No reports found</h3><p>Try another search or remove a filter.</p><button className="text-button" onClick={() => { setSearch(''); setCategoryFilter('All categories'); setTypeFilter('ALL') }}>Clear filters</button></div>}
        </> : <ResourceView view={view} rows={resourceRows} online={backendOnline} onSignIn={() => setAuthOpen(true)} onMarkRead={markAlertRead} onDecide={decideModeration} />}
      </main>

      <footer className="site-footer"><span>CampusConnect · Made for the things that matter.</span><span className="footer-campus">A little more found, together <b>✳</b></span></footer>
      </div>

      {notice && <div className="toast" role="status"><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss message">×</button></div>}
      {authOpen && <AuthDialog onClose={() => { setAuthOpen(false); setAuthError('') }} onSubmit={submitAuth} error={authError} />}
      {reportOpen && <ReportDialog initialType={reportType} onClose={() => setReportOpen(false)} onSubmit={submitReport} />}
    </div>
  )
}

function AuthDialog({ onClose, onSubmit, error }) {
  const [mode, setMode] = useState('login')
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="auth-title"><button className="dialog-close" onClick={onClose} aria-label="Close">×</button><p className="eyebrow muted">CAMPUSCONNECT ACCOUNT</p><h2 id="auth-title">{mode === 'login' ? 'Welcome back.' : 'Join your campus.'}</h2><p className="dialog-subtitle">{mode === 'login' ? 'Sign in to manage reports and claims.' : 'Create an account to help bring things home.'}</p><form onSubmit={onSubmit} className="stack-form"><input type="hidden" name="mode" value={mode === 'login' ? 'login' : 'register'} />{mode === 'register' && <label>Your name<input name="name" autoComplete="name" required maxLength="120" /></label>}<label>Campus email<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength="8" required /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="form-submit">{mode === 'login' ? 'Sign in' : 'Create account'} <span aria-hidden="true">↗</span></button></form><p className="switch-mode">{mode === 'login' ? 'New here?' : 'Already have an account?'} <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p></section></div>
}

function ReportDialog({ initialType, onClose, onSubmit }) {
  const [itemType, setItemType] = useState(initialType)
  const [imageName, setImageName] = useState('')
  const [imagePreview, setImagePreview] = useState('')
  const [imageError, setImageError] = useState('')
  useEffect(() => () => { if (imagePreview) URL.revokeObjectURL(imagePreview) }, [imagePreview])

  function chooseImage(event) {
    const file = event.target.files?.[0]
    setImageError('')
    if (!file) {
      setImageName('')
      setImagePreview('')
      return
    }
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
      setImageError('Choose a JPEG, PNG, or WebP image no larger than 5 MB.')
      event.target.value = ''
      setImageName('')
      setImagePreview('')
      return
    }
    setImageName(file.name)
    setImagePreview(URL.createObjectURL(file))
  }

  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}><section className="dialog report-dialog" role="dialog" aria-modal="true" aria-labelledby="report-title"><button className="dialog-close" onClick={onClose} aria-label="Close">×</button><p className="eyebrow muted">HELP SOMETHING FIND ITS WAY</p><h2 id="report-title">Post a report.</h2><p className="dialog-subtitle">Keep one identifying detail private for ownership verification.</p><form onSubmit={onSubmit} className="stack-form"><div className="form-two"><label>Report type<select name="item_type" value={itemType} onChange={(event) => setItemType(event.target.value)}><option value="LOST">I lost something</option><option value="FOUND">I found something</option></select></label><label>Category<select name="category" required><option value="">Choose one</option>{categories.map((category) => <option value={category} key={category}>{category}</option>)}</select></label></div><label>Item name<input name="title" required maxLength="160" placeholder="A short, recognizable title" /></label><label>Where was it last seen / found?<input name="location" required maxLength="200" placeholder="Building, room, or campus area" /></label><div className="form-two"><label>Date<input name="event_date" type="date" required max={today} /></label><label>Photo <span className="optional-label">optional · 5 MB max</span><input name="image" type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseImage} /></label></div>{imageError && <p className="form-error" role="alert">{imageError}</p>}{imagePreview && <div className="upload-preview"><img src={imagePreview} alt="Selected item preview" /><span>{imageName}</span></div>}<label>Description<textarea name="description" required maxLength="2000" rows="3" placeholder="Color, brand, or other helpful details" /></label><button className="form-submit">Publish report <span aria-hidden="true">↗</span></button></form></section></div>
}

function ResourceView({ view, rows, online, onSignIn, onMarkRead, onDecide }) {
  const descriptions = { Matches: 'Possible connections between lost and found reports. A match is a suggestion, never proof of ownership.', Messages: 'Private conversations linked to item reports.', Alerts: 'Updates about your reports, possible matches, and claims.', 'Admin dashboard': 'Review campus activity and flagged claims.' }
  const isSignedOut = ['My reports', 'Messages', 'Alerts', 'Admin dashboard'].includes(view) && !online && !rows.length
  const titleFor = (row) => view === 'Matches' ? `Possible match: ${row.lost_title} / ${row.found_title}` : row.title || row.message || row.item_title || row.status || view
  const descriptionFor = (row) => view === 'Matches' ? `${row.lost_location} · ${row.found_location}` : row.description || row.message || row.last_message || row.item?.title || (typeof row.status === 'number' ? 'Current campus total' : row.status) || 'CampusConnect update'
  const statusFor = (row) => view === 'Matches' ? `${Math.round(row.match_score)}% relevance` : row.status || (row.is_read ? 'Read' : 'New')
  return <section className="resource-panel"><p className="resource-intro">{descriptions[view]}</p>{view === 'Matches' && online && <p className="match-disclaimer">A relevance score is a suggestion only. Ownership is confirmed through a private claim review.</p>}{!online && <div className="resource-empty"><span className="empty-mark">✳</span><h3>{isSignedOut ? 'Sign in to see your activity.' : 'Your campus activity will appear here.'}</h3><p>Connect to the CampusConnect API to load private updates.</p><button className="report-button" onClick={onSignIn}>Sign in</button></div>}{online && !rows.length && <div className="resource-empty"><span className="empty-mark">✳</span><h3>Nothing here yet.</h3><p>New updates will show up as your campus community uses CampusConnect.</p></div>}{online && rows.map((row) => <article className="resource-row" key={`${row.kind || view}-${row.id}`}><span className="resource-dot" /><div><h3>{titleFor(row)}</h3><p>{descriptionFor(row)}</p></div><span className="resource-status">{statusFor(row)}</span>{view === 'Alerts' && !row.is_read && <button className="text-button" onClick={() => onMarkRead(row.id)}>Mark read</button>}{view === 'Admin dashboard' && row.kind === 'claim' && <><button className="text-button" onClick={() => onDecide(row, 'APPROVED')}>Approve</button><button className="text-button" onClick={() => onDecide(row, 'REJECTED')}>Reject</button></>}{view === 'Admin dashboard' && row.kind === 'report' && <><button className="text-button" onClick={() => onDecide(row, 'RESOLVED')}>Resolve</button><button className="text-button" onClick={() => onDecide(row, 'DISMISSED')}>Dismiss</button></>}</article>)}</section>
}

export default App