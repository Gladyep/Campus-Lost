import { useEffect, useState } from 'react'
import { createClaim, decideClaim } from './api/claims.js'
import { login, register } from './api/auth.js'
import { getItems, createItem, updateItem, deleteItem } from './api/items.js'
import { getResource, getResourceCount, getNotifications, getUnreadNotificationCount, markNotificationRead, markAllNotificationsRead, deleteNotification, clearReadNotifications, decideReport } from './api/resources.js'
import VisualSearch from './VisualSearch.jsx'
import LostItemSearch from './LostItemSearch.jsx'
import { request } from './api/client.js'
import './Campus.css'

const navigation = ['Discover', 'My reports', 'Matches', 'Visual Search', 'Lost Item Search', 'Messages', 'Alerts']
const categories = ['Electronics', 'Bags', 'Keys', 'Accessories', 'Books', 'Clothing', 'Other']
const today = new Date().toISOString().slice(0, 10)
const authStorageKey = 'campusconnect.auth'

function readSavedAuth() {
  try {
    return JSON.parse(localStorage.getItem(authStorageKey) || 'null')
  } catch {
    return null
  }
}

function saveAuth(auth) {
  if (auth) localStorage.setItem(authStorageKey, JSON.stringify(auth))
  else localStorage.removeItem(authStorageKey)
}

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

function itemIsOwnedBy(item, user) {
  if (item?.is_reporter === true) return true
  return user?.id != null && item?.reporter_id != null && String(user.id) === String(item.reporter_id)
}

function openNativeDatePicker(event) {
  const input = event.target
  if (input instanceof HTMLInputElement && input.type === 'date') {
    try {
      input.showPicker?.()
    } catch {
      // The browser may already have opened the native picker.
    }
  }
}

function App() {
  const [view, setView] = useState('Discover')
  const [items, setItems] = useState([])
  const [resourceRows, setResourceRows] = useState([])
  const [notificationUnreadCount, setNotificationUnreadCount] = useState(0)
  const [notificationCategory, setNotificationCategory] = useState('all')
  const [notificationPage, setNotificationPage] = useState(1)
  const [notificationTotal, setNotificationTotal] = useState(0)
  const [notificationHasNext, setNotificationHasNext] = useState(false)
  const [notificationHasPrevious, setNotificationHasPrevious] = useState(false)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [categoryFilter, setCategoryFilter] = useState('All categories')
  const [auth, setAuth] = useState(readSavedAuth)
  const [authOpen, setAuthOpen] = useState(false)
  const [reportOpen, setReportOpen] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [deletingItemId, setDeletingItemId] = useState(null)
  const [authError, setAuthError] = useState('')
  const [notice, setNotice] = useState('')
  const [backendOnline, setBackendOnline] = useState(false)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [summary, setSummary] = useState(null)
  const [summaryRefresh, setSummaryRefresh] = useState(0)
  const [resourceRefresh, setResourceRefresh] = useState(0)
  const [reportRefresh, setReportRefresh] = useState(0)
  const [selectedConversationId, setSelectedConversationId] = useState(null)
  const [reportType, setReportType] = useState('LOST')
  const navItems = auth?.user?.role === 'ADMIN' ? [...navigation, 'Admin dashboard'] : navigation

  useEffect(() => {
    if (!auth?.access) return undefined
    let active = true
    request('auth/profile/', { token: auth.access }).then((user) => {
      if (!active) return
      const saved = readSavedAuth() || auth
      const updated = { ...saved, user }
      saveAuth(updated)
      setAuth(updated)
    }).catch((error) => {
      if (!active || error.status !== 401) return
      saveAuth(null)
      setAuth(null)
      setNotice('Your session expired. Please sign in again.')
    })
    return () => { active = false }
  }, [auth?.access])

  useEffect(() => {
    if (!auth?.access) {
      setNotificationUnreadCount(0)
      return undefined
    }
    let active = true
    const refreshUnreadCount = () => {
      getUnreadNotificationCount(auth.access).then(({ count }) => {
        if (active) setNotificationUnreadCount(count || 0)
      }).catch(() => {})
    }
    refreshUnreadCount()
    const intervalId = window.setInterval(refreshUnreadCount, 30000)
    window.addEventListener('focus', refreshUnreadCount)
    return () => {
      active = false
      window.clearInterval(intervalId)
      window.removeEventListener('focus', refreshUnreadCount)
    }
  }, [auth?.access])

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
  }, [auth?.access, summaryRefresh])

  useEffect(() => {
    if (view === 'Visual Search' || view === 'Lost Item Search') {
      setLoading(false)
      setLoadError('')
      return undefined
    }

    let active = true
    const load = async () => {
      if (view === 'My reports' && !auth?.access) {
        setItems([])
        setBackendOnline(false)
        setLoading(false)
        return
      }
      if (['Matches', 'Messages', 'Alerts', 'Admin dashboard'].includes(view) && !auth?.access) {
        setResourceRows([])
        setBackendOnline(false)
        setLoading(false)
        setLoadError('Sign in to view your private campus activity.')
        return
      }
      setLoading(true)
      setLoadError('')
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
                } else if (view === 'Alerts') {
          const params = new URLSearchParams({ page: String(notificationPage) })
          if (notificationCategory !== 'all') params.set('category', notificationCategory)
          const result = await getNotifications(params, auth?.access)
          if (active) {
            setResourceRows(result.rows)
            setNotificationTotal(result.count)
            setNotificationHasNext(Boolean(result.next))
            setNotificationHasPrevious(Boolean(result.previous))
            setBackendOnline(true)
          }
        } else {
          const endpoints = { Matches: 'matches/', Messages: 'conversations/', 'Admin dashboard': 'admin/dashboard/' }
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
      } catch (error) {
        if (active) {
          setBackendOnline(false)
          setLoadError(error.message || 'Could not connect to the CampusConnect API.')
          if (view === 'Discover' || view === 'My reports') setItems([])
          else setResourceRows([])
          if (error.status === 401) {
            saveAuth(null)
            setAuth(null)
          }
        }
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [view, search, typeFilter, categoryFilter, auth?.access, resourceRefresh, reportRefresh, notificationCategory, notificationPage])

  useEffect(() => {
    if (!auth?.access || !['Matches', 'Messages', 'Alerts'].includes(view)) return undefined
    const refresh = () => setResourceRefresh((count) => count + 1)
    const intervalId = window.setInterval(refresh, view === 'Alerts' ? 30000 : 60000)
    window.addEventListener('focus', refresh)
    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener('focus', refresh)
    }
  }, [view, auth?.access])

  useEffect(() => {
    if (!notice) return undefined
    const timeoutId = window.setTimeout(() => setNotice(''), 4500)
    return () => window.clearTimeout(timeoutId)
  }, [notice])

  const visibleItems = items

  function browseRecentReports() {
    setView('Discover')
    setSearch('')
    setTypeFilter('ALL')
    setCategoryFilter('All categories')
    setReportRefresh((count) => count + 1)
    document.getElementById('recent-reports')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function submitAuth(event) {
    event.preventDefault()
    setAuthError('')
    const form = new FormData(event.currentTarget)
    try {
      const result = form.get('mode') === 'register'
        ? await register({ name: form.get('name'), email: form.get('email'), password: form.get('password') })
        : await login({ email: form.get('email'), password: form.get('password') })
      const nextAuth = { access: result.access, refresh: result.refresh, user: result.user || { name: form.get('name') || form.get('email'), role: 'USER' } }
      saveAuth(nextAuth)
      setAuth(nextAuth)
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
      const updatedItem = editingItem ? await updateItem(editingItem.id, form, auth.access) : null
      if (!editingItem) await createItem(form, auth.access)
      if (updatedItem) {
        setItems((rows) => rows.map((item) => String(item.id) === String(updatedItem.id) ? updatedItem : item))
      }
      setReportOpen(false)
      setEditingItem(null)
      setSummaryRefresh((count) => count + 1)
      if (!updatedItem) setView('My reports')
      setNotice(updatedItem ? 'Report updated.' : 'Your report is live. We will look for possible matches.')
    } catch (error) {
      setNotice(error.message)
    }
  }

  function editReport(item) {
    setEditingItem(item)
    setReportType(item.item_type)
    setReportOpen(true)
  }

  async function deleteReport(item) {
    if (deletingItemId === String(item.id)) return false
    if (!auth?.access) {
      setAuthOpen(true)
      setNotice('Sign in to delete your report.')
      return false
    }
    if (!itemIsOwnedBy(item, auth.user)) {
      setNotice('Only the report owner can delete this report.')
      return false
    }
    if (!window.confirm('Delete this report? This cannot be undone.')) return false

    const itemId = String(item.id)
    setDeletingItemId(itemId)
    try {
      await deleteItem(item.id, auth.access)
      setItems((rows) => rows.filter((row) => String(row.id) !== itemId))
      setSummaryRefresh((count) => count + 1)
      setNotice('Report deleted.')
      return true
    } catch (error) {
      setNotice(error.message || 'Could not delete this report. It has not been removed.')
      return false
    } finally {
      setDeletingItemId(null)
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
      const conversation = await request('conversations/', { method: 'POST', body: JSON.stringify({ item: item.id }), token: auth.access })
      setSelectedConversationId(conversation.id)
      setResourceRows([])
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
      return false
    }
    const ok = window.confirm('Confirm marking this report as recovered. This will archive it from active lists.')
    if (!ok) return false
    try {
      const updated = await request(`items/${item.id}/recover/`, { method: 'POST', token: auth.access })
      setItems((rows) => rows.map((r) => (r.id === updated.id ? updated : r)))
      setSummaryRefresh((count) => count + 1)
      setNotice('Report marked as recovered.')
      return true
    } catch (error) {
      setNotice(error.message)
      return false
    }
  }

  async function markAlertRead(id) {
    const notification = resourceRows.find((row) => String(row.id) === String(id))
    if (!notification || notification.is_read) return
    try {
      await markNotificationRead(id, auth?.access)
      setResourceRows((rows) => rows.map((row) => row.id === id ? { ...row, is_read: true } : row))
      setNotificationUnreadCount((count) => Math.max(0, count - 1))
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function markAllAlertsRead() {
    try {
      await markAllNotificationsRead(auth?.access)
      setResourceRows((rows) => rows.map((row) => ({ ...row, is_read: true })))
      setNotificationUnreadCount(0)
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function deleteAlert(notification) {
    try {
      await deleteNotification(notification.id, auth?.access)
      setResourceRows((rows) => rows.filter((row) => String(row.id) !== String(notification.id)))
      setNotificationTotal((count) => Math.max(0, count - 1))
      if (!notification.is_read) setNotificationUnreadCount((count) => Math.max(0, count - 1))
      if (resourceRows.length === 1 && notificationPage > 1) setNotificationPage((page) => page - 1)
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function clearReadAlerts() {
    if (!window.confirm('Delete all read notifications?')) return
    try {
      await clearReadNotifications(auth?.access)
      setResourceRows((rows) => rows.filter((row) => !row.is_read))
      setResourceRefresh((count) => count + 1)
    } catch (error) {
      setNotice(error.message)
    }
  }

  function openNotification(row) {
    if (!row.is_read) markAlertRead(row.id).catch((error) => setNotice(error.message))
    if (row.conversation) {
      setSelectedConversationId(row.conversation)
      setResourceRows([])
      setView('Messages')
    } else if (row.match) {
      setResourceRows([])
      setView('Matches')
    } else if (row.moderation_report && auth?.user?.role === 'ADMIN') {
      setResourceRows([])
      setView('Admin dashboard')
    } else if (row.item) {
      setSearch(row.item_title || '')
      setCategoryFilter('All categories')
      setTypeFilter(row.item_status === 'RECOVERED' ? 'RECOVERED' : 'ALL')
      setResourceRows([])
      setView('Discover')
    } else if (row.claim_item) {
      setSearch(row.claim_item_title || '')
      setResourceRows([])
      setView('Discover')
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
    <div className="app-shell" onClickCapture={openNativeDatePicker}>
      <header className="topbar">
        <a className="brand" href="#discover" onClick={() => setView('Discover')} aria-label="CampusConnect home">
          <span className="brand-mark">cc</span><span>campus<span className="brand-light">connect</span></span>
        </a>
        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map((label, index) => <button key={label} className={view === label ? 'nav-link active' : 'nav-link'} onClick={() => { setResourceRows([]); setLoadError(''); if (label === 'Alerts') setNotificationPage(1); if (label !== 'Messages') setSelectedConversationId(null); setView(label) }}><span className="nav-icon" aria-hidden="true">{['⌂', '▤', '⌕', '▧', '⌕', '✉', '◉', '◆'][index]}</span>{label === 'Alerts' ? <>Alerts{notificationUnreadCount > 0 && <span className="notification-nav-badge" aria-label={`${notificationUnreadCount} unread notifications`}>{notificationUnreadCount > 99 ? '99+' : notificationUnreadCount}</span>}</> : label}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <p className="sidebar-note">Helping our campus find its way back.</p>
          <div className="account-area">
            {auth ? <><span className="user-name">{auth.user?.name || auth.user?.email}</span><button className="text-button" onClick={() => { saveAuth(null); setAuth(null); setSummary(null); setItems([]); setResourceRows([]); setSelectedConversationId(null); setView('Discover') }}>Sign out</button></> : <button className="sign-in" onClick={() => setAuthOpen(true)}>Sign in <span aria-hidden="true">↗</span></button>}
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
            <button className="quick-action quick-browse" onClick={browseRecentReports}><span className="quick-action-mark" aria-hidden="true">⌕</span><span>Browse recent reports</span><span className="quick-arrow" aria-hidden="true">↗</span></button>
          </section>
        </>}

      <main className="content-wrap">
        <div className="context-row"><div><p className="eyebrow muted">{view === 'Discover' ? 'THE COMMUNITY BOARD' : 'YOUR CAMPUS SPACE'}</p><h2>{pageTitle}<span className="heading-period">.</span></h2></div><div className="context-meta"><span className={backendOnline ? 'connection-state online' : 'connection-state'}><i />{loading ? 'Connecting…' : backendOnline ? 'Live campus feed' : 'API unavailable'}</span><span className="context-date">Updated just now</span></div></div>

        {view === 'Visual Search' ? <VisualSearch auth={auth} onSignIn={() => setAuthOpen(true)} onClaim={claimItem} onContactReporter={contactReporter} onEditReport={editReport} onDeleteReport={deleteReport} onMarkRecovered={markRecovered} deletingItemId={deletingItemId} /> : view === 'Lost Item Search' ? <LostItemSearch auth={auth} onSignIn={() => setAuthOpen(true)} onClaim={claimItem} onContactReporter={contactReporter} onEditReport={editReport} onDeleteReport={deleteReport} onMarkRecovered={markRecovered} deletingItemId={deletingItemId} /> : view === 'Discover' || (view === 'My reports' && auth) ? <>
          <div className="toolbar"><label className="search-box"><span aria-hidden="true">⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search an item, place, or detail" aria-label="Search reports" /><kbd>/</kbd></label><label className="category-select"><span className="sr-only">Filter by category</span><select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}><option>All categories</option>{categories.map((category) => <option key={category}>{category}</option>)}</select></label><button className="report-button" onClick={() => { setReportType('LOST'); setReportOpen(true) }}><span aria-hidden="true">＋</span> Report an item</button></div>
          <div className="filter-row"><div className="segmented" role="group" aria-label="Filter by report type">{[['ALL', 'Everything'], ['LOST', 'Lost'], ['FOUND', 'Found'], ['RECOVERED', 'Recovered']].map(([value, label]) => <button key={value} className={typeFilter === value ? 'segment selected' : 'segment'} onClick={() => setTypeFilter(value)}>{label}</button>)}</div><span className="result-count">{loading ? 'Updating…' : `${visibleItems.length} reports`}</span></div>
          {loading && <div className="resource-empty" role="status"><h3>{view === 'My reports' ? 'Loading your reports…' : 'Loading community reports…'}</h3></div>}
          {loadError && (view === 'Discover' || view === 'My reports') && <div className="resource-empty" role="alert"><h3>{view === 'My reports' ? 'Could not load your reports' : 'Could not load community reports'}</h3><p>{loadError}</p></div>}
          <section id="recent-reports" className="item-grid" aria-label="Recent lost and found reports" tabIndex={-1}>
            {visibleItems.map((item, index) => {
              const isOwner = itemIsOwnedBy(item, auth?.user)
              const isActive = !['RECOVERED', 'RETURNED', 'CLOSED'].includes(item.status)
              const isDeleting = deletingItemId === String(item.id)
              return <article className="item-card" key={item.id} style={{ '--card-delay': `${index * 55}ms` }}>
                <div className="item-image-wrap">{itemImage(item) ? <img className="item-image" src={itemImage(item)} alt={item.title} loading="lazy" /> : <div className={`image-placeholder tone-${index % 4}`} aria-hidden="true"><span>{(item.category_name || 'Campus').slice(0, 1)}</span></div>}<span className={`type-tag ${item.item_type === 'FOUND' ? 'found' : 'lost'}`}><i />{item.item_type === 'FOUND' ? 'Found' : 'Lost'}</span><span className="image-date">{dateLabel(item.event_date)}</span></div>
                <div className="item-card-body"><div className="item-category">{item.category_name || item.category?.name || 'Campus item'}</div><h3>{item.title}</h3><p className="item-location"><span aria-hidden="true">⌖</span>{item.location}</p><p className="item-description">{item.description}</p><div className="item-card-footer"><span>{item.status === 'RETURNED' ? 'Reunited' : 'Campus report'}</span>{item.status === 'RECOVERED' && <span className="status-badge recovered">Recovered</span>}
                  {isOwner ? <div className="report-owner-actions">
                    {isActive && <button className="claim-link" type="button" onClick={() => editReport(item)}>Edit Report</button>}
                    <button className="delete-report-button" type="button" disabled={isDeleting} onClick={() => deleteReport(item)}>{isDeleting ? 'Deleting…' : 'Delete Report'}</button>
                    {isActive && <button className="text-button" type="button" onClick={() => markRecovered(item)}>Mark recovered</button>}
                  </div> : <>
                    {item.item_type === 'FOUND' && item.status === 'OPEN' && <button className="claim-link" type="button" onClick={() => claimItem(item)}>That might be mine <span aria-hidden="true">↗</span></button>}
                    {isActive && <button className="claim-link" type="button" onClick={() => contactReporter(item)}>Contact reporter <span aria-hidden="true">↗</span></button>}
                  </>}</div></div>
              </article>
            })}
          </section>
          {backendOnline && !visibleItems.length && <div className="empty-state"><span className="empty-mark">⌕</span><h3>No reports found</h3><p>Try another search or remove a filter.</p><button className="text-button" onClick={() => { setSearch(''); setCategoryFilter('All categories'); setTypeFilter('ALL') }}>Clear filters</button></div>}
        </> : <ResourceView view={view} rows={resourceRows} online={backendOnline} loading={loading} error={loadError} authenticated={Boolean(auth?.access)} auth={auth} onSignIn={() => setAuthOpen(true)} onMarkRead={markAlertRead} onOpenNotification={openNotification} onMarkAllRead={markAllAlertsRead} onDeleteAlert={deleteAlert} onClearRead={clearReadAlerts} notificationUnreadCount={notificationUnreadCount} notificationCategory={notificationCategory} onNotificationCategoryChange={(category) => { setNotificationCategory(category); setNotificationPage(1) }} notificationPage={notificationPage} notificationTotal={notificationTotal} notificationHasNext={notificationHasNext} notificationHasPrevious={notificationHasPrevious} onNotificationPageChange={setNotificationPage} onDecide={decideModeration} onContactReporter={contactReporter} selectedConversationId={selectedConversationId} />}
      </main>

      <footer className="site-footer"><span>CampusConnect · Made for the things that matter.</span><span className="footer-campus">A little more found, together <b>✳</b></span></footer>
      </div>

      {notice && <div className="toast" role="status"><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss message">×</button></div>}
      {authOpen && <AuthDialog onClose={() => { setAuthOpen(false); setAuthError('') }} onSubmit={submitAuth} error={authError} />}
      {reportOpen && <ReportDialog initialType={reportType} initialItem={editingItem} onClose={() => { setReportOpen(false); setEditingItem(null) }} onSubmit={submitReport} />}
    </div>
  )
}

function AuthDialog({ onClose, onSubmit, error }) {
  const [mode, setMode] = useState('login')
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="auth-title"><button className="dialog-close" onClick={onClose} aria-label="Close">×</button><p className="eyebrow muted">CAMPUSCONNECT ACCOUNT</p><h2 id="auth-title">{mode === 'login' ? 'Welcome back.' : 'Join your campus.'}</h2><p className="dialog-subtitle">{mode === 'login' ? 'Sign in to manage reports and claims.' : 'Create an account to help bring things home.'}</p><form onSubmit={onSubmit} className="stack-form"><input type="hidden" name="mode" value={mode === 'login' ? 'login' : 'register'} />{mode === 'register' && <label>Your name<input name="name" autoComplete="name" required maxLength="120" /></label>}<label>Campus email<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength="8" required /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="form-submit">{mode === 'login' ? 'Sign in' : 'Create account'} <span aria-hidden="true">↗</span></button></form><p className="switch-mode">{mode === 'login' ? 'New here?' : 'Already have an account?'} <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p></section></div>
}

function ReportDialog({ initialType, initialItem, onClose, onSubmit }) {
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

  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}><section className="dialog report-dialog" role="dialog" aria-modal="true" aria-labelledby="report-title"><button className="dialog-close" onClick={onClose} aria-label="Close">×</button><p className="eyebrow muted">HELP SOMETHING FIND ITS WAY</p><h2 id="report-title">{initialItem ? 'Edit report.' : 'Post a report.'}</h2><p className="dialog-subtitle">Keep one identifying detail private for ownership verification.</p><form onSubmit={onSubmit} className="stack-form"><div className="form-two"><label>Report type<select name="item_type" value={itemType} onChange={(event) => setItemType(event.target.value)}><option value="LOST">I lost something</option><option value="FOUND">I found something</option></select></label><label>Category<select name="category" defaultValue={initialItem?.category_name || initialItem?.category?.name || initialItem?.category || ''} required><option value="">Choose one</option>{categories.map((category) => <option value={category} key={category}>{category}</option>)}</select></label></div><label>Item name<input name="title" defaultValue={initialItem?.title || ''} required maxLength="160" placeholder="A short, recognizable title" /></label><label>Where was it last seen / found?<input name="location" defaultValue={initialItem?.location || ''} required maxLength="200" placeholder="Building, room, or campus area" /></label><div className="form-two"><label>Date<input name="event_date" type="date" defaultValue={initialItem?.event_date || ''} required max={today} /></label><label>Photo <span className="optional-label">optional · 5 MB max</span><input name="image" type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseImage} /></label></div>{imageError && <p className="form-error" role="alert">{imageError}</p>}{imagePreview && <div className="upload-preview"><img src={imagePreview} alt="Selected item preview" /><span>{imageName}</span></div>}<label>Description<textarea name="description" defaultValue={initialItem?.description || ''} required maxLength="2000" rows="3" placeholder="Color, brand, or other helpful details" /></label><button className="form-submit">{initialItem ? 'Save changes' : 'Publish report'} <span aria-hidden="true">↗</span></button></form></section></div>
}

function MessagesPanel({ rows, auth, loading, error, selectedConversationId }) {
  const [conversationId, setConversationId] = useState(selectedConversationId)
  const [messages, setMessages] = useState([])
  const [messageError, setMessageError] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    const nextId = selectedConversationId || rows[0]?.id
    setConversationId(nextId || null)
  }, [rows, selectedConversationId])

  useEffect(() => {
    if (!conversationId || !auth?.access) {
      setMessages([])
      return undefined
    }
    let active = true
    setMessageError('')
    request(`conversations/${conversationId}/messages/`, { token: auth.access }).then((result) => {
      if (active) setMessages(Array.isArray(result) ? result : [])
    }).catch((requestError) => {
      if (active) {
        setMessages([])
        setMessageError(requestError.message || 'Could not load this conversation.')
      }
    })
    return () => { active = false }
  }, [conversationId, auth?.access])

  async function sendMessage(event) {
    event.preventDefault()
    const form = event.currentTarget
    const text = new FormData(form).get('message_text')?.toString().trim()
    if (!text || text.length > 2000 || sending || !conversationId) return
    setSending(true)
    setMessageError('')
    try {
      const message = await request(`conversations/${conversationId}/messages/`, {
        method: 'POST',
        body: JSON.stringify({ message_text: text }),
        token: auth.access,
      })
      setMessages((current) => [...current, message])
      form.reset()
    } catch (requestError) {
      setMessageError(requestError.message || 'Message was not sent. Try again.')
    } finally {
      setSending(false)
    }
  }

  const activeConversation = rows.find((row) => row.id === conversationId)
  if (loading) return <section className="resource-panel"><div className="resource-empty" role="status"><h3>Loading conversations…</h3></div></section>
  if (error) return <section className="resource-panel"><div className="resource-empty" role="alert"><h3>Could not load conversations</h3><p>{error}</p></div></section>
  if (!rows.length) return <section className="resource-panel"><div className="resource-empty"><span className="empty-mark">✉</span><h3>No conversations yet</h3><p>Contact a report owner or reporter to start a private conversation.</p></div></section>

  return <section className="messages-layout" aria-label="Private messages">
    <nav className="conversation-list" aria-label="Conversations">{rows.map((row) => <button key={row.id} type="button" className={row.id === conversationId ? 'conversation-choice active' : 'conversation-choice'} onClick={() => setConversationId(row.id)}><strong>{row.other_participant_name || 'Campus member'}</strong><span>{row.item_title || 'Item report'}</span><small>{row.last_message || 'No messages yet'}</small></button>)}</nav>
    <section className="conversation-thread" aria-label={activeConversation?.item_title || 'Conversation'}>
      <header className="conversation-heading"><div><h3>{activeConversation?.other_participant_name || 'Campus member'}</h3><p>{activeConversation?.item_title || 'Item report'}</p></div></header>
      {messageError && <p className="message-error" role="alert">{messageError}</p>}
      <div className="message-list" aria-live="polite">{messages.map((message) => <article key={message.id} className={message.sender === auth?.user?.id ? 'message-bubble sent' : 'message-bubble received'}><p>{message.message_text}</p><small>{message.sender_name} · {message.sent_at ? new Date(message.sent_at).toLocaleString() : ''}</small></article>)}{!messages.length && !messageError && <p className="thread-empty">No messages yet. Start the conversation below.</p>}</div>
      <form className="message-compose" onSubmit={sendMessage}><label className="sr-only" htmlFor="message-text">Message</label><textarea id="message-text" name="message_text" required maxLength="2000" rows="2" placeholder="Write a message…" /><button className="report-button" type="submit" disabled={sending}>{sending ? 'Sending…' : 'Send'}</button></form>
    </section>
  </section>
}

function MatchesPanel({ rows, auth, loading, error, authenticated, onSignIn, onContactReporter }) {
  const [detailsId, setDetailsId] = useState(null)
  if (!authenticated && !loading) return <section className="resource-panel"><div className="resource-empty"><h3>Sign in to see your matches.</h3><p>Possible matches are calculated from active community reports.</p><button className="report-button" onClick={onSignIn}>Sign in</button></div></section>
  if (loading) return <section className="resource-panel"><div className="resource-empty" role="status"><h3>Finding possible matches…</h3></div></section>
  if (error) return <section className="resource-panel"><div className="resource-empty" role="alert"><h3>Could not load matches</h3><p>{error}</p></div></section>
  if (!rows.length) return <section className="resource-panel"><p className="resource-intro">Possible connections between lost and found reports. A match is a suggestion, never proof of ownership.</p><div className="resource-empty"><h3>No potential matches yet</h3><p>New suggestions will appear when active lost and found reports share useful details.</p></div></section>

  return <section className="matches-panel"><p className="match-disclaimer">A match is only a suggestion. Confirm ownership through a private conversation and claim review.</p>{rows.map((match) => {
    const userId = auth?.user?.id
    const contactFound = match.lost_reporter_id === userId
    const contactItem = contactFound ? match.found_item : match.lost_item
    const contactTitle = contactFound ? match.found_title : match.lost_title
    const detailOpen = detailsId === match.id
    return <article className="match-card" key={match.id}>
      <header className="match-card-heading"><div><span className="match-score">{Math.round(match.match_score)}% relevance</span><h3>Possible report connection</h3></div><span className="match-disclaimer-label">Suggestion only</span></header>
      <div className="match-reports">{[['Lost report', 'lost'], ['Found report', 'found']].map(([label, prefix]) => <div className="match-report" key={prefix}>{match[`${prefix}_image`] ? <img src={match[`${prefix}_image`]} alt={match[`${prefix}_title`]} loading="lazy" /> : <div className="match-image-placeholder" aria-hidden="true">{prefix === 'lost' ? '−' : '+'}</div>}<div><span>{label} · {match[`${prefix}_category`]}</span><h4>{match[`${prefix}_title`]}</h4><p>{match[`${prefix}_location`]} · {dateLabel(match[`${prefix}_event_date`])}</p><small>{match[`${prefix}_status`]?.replaceAll('_', ' ')}</small></div></div>)}</div>
      {detailOpen && <div className="match-details"><p><strong>Lost report:</strong> {match.lost_description}</p><p><strong>Found report:</strong> {match.found_description}</p></div>}
      <footer className="match-card-actions"><button className="visual-detail-button" type="button" onClick={() => setDetailsId(detailOpen ? null : match.id)}>{detailOpen ? 'Hide Details' : 'View Details'}</button><button className="report-button" type="button" onClick={() => onContactReporter({ id: contactItem, title: contactTitle })}>Contact Reporter</button></footer>
    </article>
  })}</section>
}

function AlertsPanel({ rows, loading, error, authenticated, auth, onSignIn, onMarkRead, onOpenNotification, onMarkAllRead, onDelete, onClearRead, unreadCount, category, onCategoryChange, page, total, hasNext, hasPrevious, onPageChange }) {
  const filters = [
    ['all', 'All'], ['lost-found', 'Lost & Found'], ['matches', 'Matches'],
    ['claims', 'Claims'], ['messages', 'Messages'], ['system', 'System Updates'],
  ]
  const icons = { REPORT: '▣', STATUS: '↻', MATCH: '⌕', CLAIM: '✓', MESSAGE: '✉', MODERATION: '◆' }

  if (!authenticated) return <section className="resource-panel"><div className="resource-empty"><span className="empty-mark">◉</span><h3>Sign in to view alerts.</h3><p>Your notifications are private to your account.</p><button className="report-button" onClick={onSignIn}>Sign in</button></div></section>
  if (loading) return <section className="resource-panel"><div className="resource-empty" role="status"><h3>Loading notifications…</h3></div></section>
  if (error) return <section className="resource-panel"><div className="resource-empty" role="alert"><h3>Could not load notifications</h3><p>{error}</p></div></section>

  return <section className="resource-panel alerts-panel" aria-label="Notification center">
    <p className="resource-intro">Updates about reports, possible matches, claims, messages, and campus reviews.</p>
    <div className="alerts-toolbar">
      <div className="alerts-filters" role="group" aria-label="Filter notifications">{filters.map(([value, label]) => <button key={value} type="button" className={category === value ? 'segment selected' : 'segment'} onClick={() => onCategoryChange(value)}>{label}</button>)}</div>
      <div className="alerts-bulk-actions"><span className="alerts-unread-count">{unreadCount} unread</span><button className="text-button" type="button" disabled={!unreadCount} onClick={onMarkAllRead}>Mark all read</button><button className="text-button" type="button" onClick={onClearRead}>Clear read</button></div>
    </div>

    {!rows.length ? <div className="resource-empty" role="status"><span className="empty-mark">◉</span><h3>{total ? 'No notifications on this page' : category === 'all' ? 'Nothing here yet.' : 'No notifications in this category.'}</h3><p>{total ? 'Use the page controls to view more notifications.' : 'Relevant campus activity will appear here when it happens.'}</p></div> : <div className="alerts-list">
      {rows.map((row) => {
        const relatedTitle = row.item_title || row.claim_item_title || (row.conversation ? 'Private conversation' : row.match ? 'Potential item match' : row.moderation_report ? 'Report review' : '')
        const canOpenModeration = Boolean(row.moderation_report && auth?.user?.role === 'ADMIN')
        const hasTarget = Boolean(row.conversation || row.match || row.item || row.claim_item || canOpenModeration)
        return <article className={`alert-card${row.is_read ? ' read' : ' unread'}`} key={row.id}>
          <span className={`alert-type-icon alert-kind-${row.kind?.toLowerCase() || 'system'}`} aria-hidden="true">{icons[row.kind] || '◆'}</span>
          <span className="alert-unread-dot" aria-label={row.is_read ? 'Read' : 'Unread'} />
          <div className="alert-content"><div className="alert-heading"><h3>{row.title || row.message || 'CampusConnect update'}</h3><time dateTime={row.created_at}>{row.created_at ? new Date(row.created_at).toLocaleString() : ''}</time></div><p>{row.message}</p>{relatedTitle && <p className="alert-related">Related: {relatedTitle}{row.item_status ? ` · ${row.item_status.replaceAll('_', ' ').toLowerCase()}` : row.claim_status ? ` · ${row.claim_status.replaceAll('_', ' ').toLowerCase()}` : ''}</p>}<div className="alert-actions">{hasTarget && <button className="visual-detail-button" type="button" onClick={() => onOpenNotification(row)}>{row.conversation ? 'Open conversation' : row.match ? 'View matches' : canOpenModeration ? 'Open review' : row.claim ? 'View claim report' : 'View report'}</button>}{!row.is_read && <button className="text-button" type="button" onClick={() => onMarkRead(row.id)}>Mark read</button>}<button className="text-button alert-delete" type="button" onClick={() => onDelete(row)}>Delete</button></div></div>
        </article>
      })}
    </div>}

    {total > 0 && <nav className="alerts-pagination" aria-label="Notification pages"><button className="visual-detail-button" type="button" disabled={!hasPrevious} onClick={() => onPageChange(Math.max(1, page - 1))}>Previous</button><span>Page {page} · {total} notifications</span><button className="visual-detail-button" type="button" disabled={!hasNext} onClick={() => onPageChange(page + 1)}>Next</button></nav>}
  </section>
}

function ResourceView({ view, rows, online, loading, error, authenticated, onSignIn, onMarkRead, onOpenNotification, onMarkAllRead, onDeleteAlert, onClearRead, notificationUnreadCount, notificationCategory, onNotificationCategoryChange, notificationPage, notificationTotal, notificationHasNext, notificationHasPrevious, onNotificationPageChange, onDecide, onContactReporter, selectedConversationId, auth }) {
  const descriptions = { Matches: 'Possible connections between lost and found reports. A match is a suggestion, never proof of ownership.', Messages: 'Private conversations linked to item reports.', Alerts: 'Updates about your reports, possible matches, and claims.', 'Admin dashboard': 'Review campus activity and flagged claims.' }
  if (view === 'Messages') return <MessagesPanel rows={rows} auth={auth} loading={loading} error={error} selectedConversationId={selectedConversationId} />
  if (view === 'Matches') return <MatchesPanel rows={rows} auth={auth} loading={loading} error={error} authenticated={authenticated} onSignIn={onSignIn} onContactReporter={onContactReporter} />
  if (view === 'Alerts') return <AlertsPanel rows={rows} loading={loading} error={error} authenticated={authenticated} auth={auth} onSignIn={onSignIn} onMarkRead={onMarkRead} onOpenNotification={onOpenNotification} onMarkAllRead={onMarkAllRead} onDelete={onDeleteAlert} onClearRead={onClearRead} unreadCount={notificationUnreadCount} category={notificationCategory} onCategoryChange={onNotificationCategoryChange} page={notificationPage} total={notificationTotal} hasNext={notificationHasNext} hasPrevious={notificationHasPrevious} onPageChange={onNotificationPageChange} />
  const titleFor = (row) => view === 'Matches' ? `Possible match: ${row.lost_title} / ${row.found_title}` : row.title || row.message || row.item_title || row.status || view
  const descriptionFor = (row) => view === 'Matches' ? `${row.lost_location} · ${row.found_location}` : row.description || row.message || row.last_message || row.item_title || row.item?.title || (typeof row.status === 'number' ? 'Current campus total' : row.status) || 'CampusConnect update'
  const statusFor = (row) => view === 'Matches' ? `${Math.round(row.match_score)}% relevance` : row.status || (row.is_read ? 'Read' : 'New')
  return <section className="resource-panel"><p className="resource-intro">{descriptions[view]}</p>{view === 'Matches' && online && <p className="match-disclaimer">A relevance score is a suggestion only. Ownership is confirmed through a private claim review.</p>}{!authenticated && !online && <div className="resource-empty"><span className="empty-mark">✳</span><h3>Sign in to see your activity.</h3><p>Your private campus activity is available after you sign in.</p><button className="report-button" onClick={onSignIn}>Sign in</button></div>}{authenticated && loading && <div className="resource-empty" role="status"><h3>Loading campus activity…</h3></div>}{authenticated && !online && !loading && <div className="resource-empty" role="alert"><h3>Could not load campus activity</h3><p>{error || 'Check that the backend is running, then try again.'}</p></div>}{online && !rows.length && <div className="resource-empty"><span className="empty-mark">✳</span><h3>Nothing here yet.</h3><p>New updates will show up as your campus community uses CampusConnect.</p></div>}{online && rows.map((row) => <article className="resource-row" key={`${row.kind || view}-${row.id}`}><span className={row.is_read === false ? 'resource-dot unread' : 'resource-dot'} /><div><h3>{view === 'Alerts' ? <button type="button" className="notification-link" onClick={() => onOpenNotification(row)}>{titleFor(row)}</button> : titleFor(row)}</h3><p>{descriptionFor(row)}</p></div><span className="resource-status">{statusFor(row)}</span>{view === 'Alerts' && !row.is_read && <button className="text-button" onClick={() => onMarkRead(row.id)}>Mark read</button>}{view === 'Admin dashboard' && row.kind === 'claim' && <><button className="text-button" onClick={() => onDecide(row, 'APPROVED')}>Approve</button><button className="text-button" onClick={() => onDecide(row, 'REJECTED')}>Reject</button></>}{view === 'Admin dashboard' && row.kind === 'report' && <><button className="text-button" onClick={() => onDecide(row, 'RESOLVED')}>Resolve</button><button className="text-button" onClick={() => onDecide(row, 'DISMISSED')}>Dismiss</button></>}</article>)}</section>
}

export default App