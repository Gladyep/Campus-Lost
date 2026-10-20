import { useState } from 'react'
import { searchFoundItems } from './api/items.js'

const categories = ['Electronics', 'Bags', 'Keys', 'Accessories', 'Books', 'Clothing', 'Other']
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

function imageUrl(item) {
  const image = item.images?.[0]?.image || ''
  if (image.startsWith('/')) return `${apiUrl.replace(/\/api\/?$/, '')}${image}`
  return image
}

function dateLabel(date) {
  if (!date) return 'Date not listed'
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${date}T12:00:00`))
}

function LostItemSearch({ auth, onSignIn, onClaim, onContactReporter, onEditReport, onDeleteReport, onMarkRecovered, deletingItemId }) {
  const [results, setResults] = useState([])
  const [searched, setSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [detailsItem, setDetailsItem] = useState(null)

  async function submitSearch(event) {
    event.preventDefault()
    if (loading) return
    const form = new FormData(event.currentTarget)
    const query = new URLSearchParams()
    for (const key of ['q', 'start_date', 'end_date', 'category', 'location']) {
      const value = String(form.get(key) || '').trim()
      if (value) query.set(key, value)
    }
    if (query.has('start_date') && query.has('end_date') && query.get('end_date') < query.get('start_date')) {
      setError('End date must be on or after the start date.')
      setResults([])
      setSearched(false)
      return
    }
    setLoading(true)
    setError('')
    setSearched(true)
    try {
      setResults(await searchFoundItems(query))
    } catch (searchError) {
      setResults([])
      setError(searchError.message || 'Could not load found reports. Try again.')
    } finally {
      setLoading(false)
    }
  }

  function clearFilters(event) {
    event.currentTarget.form.reset()
    setResults([])
    setSearched(false)
    setError('')
  }

  async function deleteResult(item) {
    if (await onDeleteReport(item)) {
      setResults((rows) => rows.filter((row) => String(row.id) !== String(item.id)))
      setDetailsItem(null)
    }
  }

  async function recoverResult(item) {
    if (await onMarkRecovered(item)) {
      setResults((rows) => rows.filter((row) => String(row.id) !== String(item.id)))
      setDetailsItem(null)
    }
  }

  return <section className="lost-search-page" aria-labelledby="lost-search-title">
    <div className="lost-search-intro">
      <p className="eyebrow muted">SEARCH COMMUNITY FOUND REPORTS</p>
      <h1 id="lost-search-title">Find Your Lost Item</h1>
      <p>Search items that other people have reported finding. You do not need to submit a lost-item report.</p>
    </div>

    <form className="lost-search-form" onSubmit={submitSearch}>
      <label className="lost-search-keyword">Keyword or item name<input name="q" type="search" maxLength="160" placeholder="Try headphones, wallet, or backpack" /></label>
      <label>Start date<input name="start_date" type="date" /></label>
      <label>End date<input name="end_date" type="date" /></label>
      <label>Category<select name="category"><option value="">All categories</option>{categories.map((category) => <option value={category} key={category}>{category}</option>)}</select></label>
      <label>Campus location<input name="location" maxLength="200" placeholder="Any campus location" /></label>
      <div className="lost-search-actions"><button className="report-button" type="submit" disabled={loading}>{loading ? 'Searching…' : 'Search found items'}</button><button className="text-button" type="button" onClick={clearFilters}>Clear filters</button></div>
    </form>

    {error && <div className="lost-search-state error" role="alert"><h2>Search could not be completed</h2><p>{error}</p></div>}
    {loading && <p className="lost-search-status" role="status">Searching found-item reports…</p>}
    {searched && !loading && !error && results.length === 0 && <div className="lost-search-state" role="status"><h2>No found reports match those filters</h2><p>Try a broader keyword, date range, or location.</p></div>}
    {results.length > 0 && <section className="lost-search-results" aria-label="Found-item search results">
      <div className="lost-results-heading"><h2>Found reports</h2><span>{results.length} result{results.length === 1 ? '' : 's'}</span></div>
      <div className="item-grid">
        {results.map((item, index) => <article className="item-card" key={item.id} style={{ '--card-delay': `${index * 45}ms` }}>
          <div className="item-image-wrap">{imageUrl(item) ? <img className="item-image" src={imageUrl(item)} alt={item.title} loading="lazy" /> : <div className={`image-placeholder tone-${index % 4}`} aria-label="No report photo"><span>{(item.category_name || 'Campus').slice(0, 1)}</span></div>}<span className="type-tag found"><i />Found</span><span className="image-date">{dateLabel(item.event_date)}</span></div>
          <div className="item-card-body"><div className="item-category">{item.category_name || item.category || 'Campus item'}</div><h3>{item.title}</h3><p className="item-location"><span aria-hidden="true">⌖</span>{item.location}</p><p className="item-description">{item.description}</p><div className="lost-result-actions"><button className="visual-detail-button" type="button" onClick={() => setDetailsItem(item)}>View Details</button>{itemIsOwnedBy(item, auth?.user) ? <><button className="claim-link" type="button" onClick={() => onEditReport(item)}>Edit Report</button><button className="delete-report-button" type="button" disabled={deletingItemId === String(item.id)} onClick={() => deleteResult(item)}>{deletingItemId === String(item.id) ? 'Deleting…' : 'Delete Report'}</button><button className="text-button" type="button" onClick={() => recoverResult(item)}>Mark recovered</button></> : <><button className="claim-link" type="button" onClick={() => auth?.access ? onClaim(item) : onSignIn()}>That might be mine</button><button className="claim-link" type="button" onClick={() => auth?.access ? onContactReporter(item) : onSignIn()}>Contact Reporter</button></>}</div></div>
        </article>)}
      </div>
    </section>}

    {detailsItem && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setDetailsItem(null) }}>
      <section className="dialog visual-details-dialog" role="dialog" aria-modal="true" aria-labelledby="lost-details-title"><button className="dialog-close" type="button" onClick={() => setDetailsItem(null)} aria-label="Close">×</button>{imageUrl(detailsItem) && <img className="visual-details-image" src={imageUrl(detailsItem)} alt={detailsItem.title} />}<p className="eyebrow muted">FOUND ITEM REPORT</p><h2 id="lost-details-title">{detailsItem.title}</h2><p className="visual-details-category">{detailsItem.category_name || detailsItem.category}</p><dl className="visual-details-list"><div><dt>Found at</dt><dd>{detailsItem.location}</dd></div><div><dt>Date reported</dt><dd>{dateLabel(detailsItem.event_date)}</dd></div><div><dt>Status</dt><dd>Found</dd></div></dl><p className="visual-details-description">{detailsItem.description}</p>{itemIsOwnedBy(detailsItem, auth?.user) ? <div className="visual-details-actions"><button className="visual-detail-button" type="button" onClick={() => onEditReport(detailsItem)}>Edit Report</button><button className="delete-report-button" type="button" disabled={deletingItemId === String(detailsItem.id)} onClick={() => deleteResult(detailsItem)}>{deletingItemId === String(detailsItem.id) ? 'Deleting…' : 'Delete Report'}</button><button className="text-button" type="button" onClick={() => recoverResult(detailsItem)}>Mark recovered</button></div> : <div className="visual-details-actions"><button className="form-submit" type="button" onClick={() => auth?.access ? onClaim(detailsItem) : onSignIn()}>That might be mine <span aria-hidden="true">↗</span></button><button className="visual-detail-button" type="button" onClick={() => auth?.access ? onContactReporter(detailsItem) : onSignIn()}>Contact Reporter</button></div>}</section>
    </div>}
  </section>
}

function itemIsOwnedBy(item, user) {
  if (item?.is_reporter === true) return true
  return user?.id != null && item?.reporter_id != null && String(user.id) === String(item.reporter_id)
}

export default LostItemSearch