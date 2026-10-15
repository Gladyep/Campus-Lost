import { useEffect, useRef, useState } from 'react'
import { searchItemsByImage } from './api/items.js'

const categories = ['Electronics', 'Bags', 'Keys', 'Accessories', 'Books', 'Clothing', 'Other']
const allowedTypes = new Set(['image/jpeg', 'image/png', 'image/webp'])
const maxFileSize = 5 * 1024 * 1024
const maxImagePixels = 16_000_000
const maxImageDimension = 4096
const today = new Date().toISOString().slice(0, 10)

function imageUrl(item) {
  return item.images?.[0]?.image || item.image_url || ''
}

function dateLabel(date) {
  if (!date) return 'Date not listed'
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${date}T12:00:00`))
}

function VisualSearch({ auth, onSignIn, onClaim }) {
  const [selectedImage, setSelectedImage] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [category, setCategory] = useState('')
  const [location, setLocation] = useState('')
  const [eventDate, setEventDate] = useState('')
  const [results, setResults] = useState([])
  const [searched, setSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const [detailsItem, setDetailsItem] = useState(null)
  const fileInput = useRef(null)
  const validationId = useRef(0)

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  function chooseImage(file) {
    if (!file) return
    const currentValidation = ++validationId.current
    setSelectedImage(null)
    setPreviewUrl('')
    setResults([])
    setSearched(false)
    setError('')

    if (!allowedTypes.has(file.type)) {
      setError('Choose a JPG, PNG, or WEBP image.')
      return
    }
    if (file.size > maxFileSize) {
      setError('Images must be 5 MB or smaller.')
      return
    }

    const nextPreviewUrl = URL.createObjectURL(file)
    const probe = new Image()
    probe.onload = () => {
      if (currentValidation !== validationId.current) {
        URL.revokeObjectURL(nextPreviewUrl)
        return
      }
      if (probe.naturalWidth > maxImageDimension || probe.naturalHeight > maxImageDimension || probe.naturalWidth * probe.naturalHeight > maxImagePixels) {
        URL.revokeObjectURL(nextPreviewUrl)
        setError('Images must be no larger than 4096 pixels per side or 16 megapixels.')
        return
      }
      setSelectedImage(file)
      setPreviewUrl(nextPreviewUrl)
    }
    probe.onerror = () => {
      URL.revokeObjectURL(nextPreviewUrl)
      if (currentValidation !== validationId.current) return
      setError('The selected file could not be decoded as an image.')
    }
    probe.src = nextPreviewUrl
  }

  function removeImage() {
    validationId.current += 1
    setSelectedImage(null)
    setPreviewUrl('')
    setResults([])
    setSearched(false)
    setError('')
    if (fileInput.current) fileInput.current.value = ''
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragging(false)
    chooseImage(event.dataTransfer.files?.[0])
  }

  async function submitSearch(event) {
    event.preventDefault()
    if (!selectedImage || loading) return
    if (!auth?.access) {
      onSignIn()
      return
    }

    const formData = new FormData()
    formData.append('image', selectedImage)
    if (category) formData.append('category', category)
    if (location.trim()) formData.append('location', location.trim())
    if (eventDate) formData.append('event_date', eventDate)

    setLoading(true)
    setError('')
    setSearched(true)
    try {
      const response = await searchItemsByImage(formData, auth.access)
      setResults(response.results || [])
    } catch (searchError) {
      setResults([])
      setError(searchError.message || 'Visual search could not be completed. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return <section className="visual-search-page" aria-labelledby="visual-search-title">
    <div className="visual-search-intro">
      <div>
        <p className="eyebrow muted">IMAGE-BASED REPORT SEARCH</p>
        <h1 id="visual-search-title">Find Your Lost Item</h1>
        <p>Upload a photo of your lost item to discover visually similar items reported on campus.</p>
      </div>
      <p className="visual-search-caveat">Similarity is approximate and is not proof of ownership.</p>
    </div>

    {!auth?.access && <div className="visual-auth-note">
      <span>Sign in to search campus reports.</span>
      <button className="text-button" type="button" onClick={onSignIn}>Sign in</button>
    </div>}

    <form className="visual-search-form" onSubmit={submitSearch}>
      <section className="visual-upload-panel" aria-label="Upload an item photo">
        <div className="visual-panel-heading"><div><p className="eyebrow muted">START WITH A PHOTO</p><h2>Upload an image</h2></div>{selectedImage && <button className="text-button" type="button" onClick={removeImage}>Remove photo</button>}</div>
        <input ref={fileInput} id="visual-image-input" className="sr-only" type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" onChange={(event) => chooseImage(event.target.files?.[0])} />
        {previewUrl ? <div className="visual-preview">
          <img src={previewUrl} alt="Preview of the selected lost item" />
          <div><strong>{selectedImage.name}</strong><span>{(selectedImage.size / (1024 * 1024)).toFixed(1)} MB · Ready to search</span></div>
          <button className="visual-replace" type="button" onClick={() => fileInput.current?.click()}>Replace</button>
        </div> : <label className={`visual-dropzone${dragging ? ' dragging' : ''}`} htmlFor="visual-image-input" onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={handleDrop}>
          <span className="visual-upload-icon" aria-hidden="true">▧</span>
          <strong>Drop a photo here or browse</strong>
          <span>JPG, PNG, or WEBP · up to 5 MB · 16 megapixels</span>
        </label>}
      </section>

      <section className="visual-filter-panel" aria-labelledby="visual-filters-title">
        <div className="visual-panel-heading"><div><p className="eyebrow muted">NARROW THE RESULTS</p><h2 id="visual-filters-title">Search filters</h2></div></div>
        <div className="visual-filter-fields">
          <label>Item category<select value={category} onChange={(event) => setCategory(event.target.value)}><option value="">All categories</option>{categories.map((name) => <option key={name} value={name}>{name}</option>)}</select></label>
          <label>Campus location<input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Any campus location" maxLength="200" /></label>
          <label>Date reported<input value={eventDate} onChange={(event) => setEventDate(event.target.value)} type="date" max={today} /></label>
        </div>
        <button className="report-button visual-search-submit" type="submit" disabled={!selectedImage || loading}>
          {loading ? <><span className="visual-spinner" aria-hidden="true" /> Searching items…</> : <>Find Similar Items <span aria-hidden="true">↗</span></>}
        </button>
      </section>
    </form>

    {error && <p className="visual-search-error" role="alert">{error}</p>}
    {loading && <p className="visual-search-status" role="status">Comparing your photo with found-item reports…</p>}
    {searched && !loading && !error && results.length === 0 && <div className="visual-empty-state" role="status"><span aria-hidden="true">⌕</span><h2>No similar items found</h2><p>Try a clearer photo or broaden your filters.</p></div>}

    {results.length > 0 && <section className="visual-results" aria-labelledby="visual-results-title">
      <div className="visual-results-heading"><div><p className="eyebrow muted">CAMPUS FOUND ITEMS</p><h2 id="visual-results-title">Visually similar reports</h2></div><span>{results.length} result{results.length === 1 ? '' : 's'}</span></div>
      <p className="visual-results-caveat">Approximate visual similarity only. A score does not confirm that an item is yours.</p>
      <div className="item-grid visual-result-grid">
        {results.map((item) => <article className="item-card visual-result-card" key={item.id}>
          <div className="item-image-wrap">
            <img className="item-image" src={imageUrl(item)} alt={item.title} loading="lazy" />
            <span className="type-tag found"><i />Found</span>
            <span className="similarity-badge">{item.similarity}% similar</span>
          </div>
          <div className="item-card-body">
            <div className="item-category">{item.category_name || item.category || 'Campus item'}</div>
            <h3>{item.title}</h3>
            <p className="item-location"><span aria-hidden="true">⌖</span>{item.location}</p>
            <p className="visual-result-date">Reported {dateLabel(item.event_date)}</p>
            <div className="visual-result-footer"><span>{item.status?.replaceAll('_', ' ') || 'Status unavailable'}</span><button className="visual-detail-button" type="button" onClick={() => setDetailsItem(item)}>View Details</button></div>
          </div>
        </article>)}
      </div>
    </section>}

    {detailsItem && <ItemDetailsDialog item={detailsItem} onClose={() => setDetailsItem(null)} onClaim={onClaim} />}
  </section>
}

function ItemDetailsDialog({ item, onClose, onClaim }) {
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <section className="dialog visual-details-dialog" role="dialog" aria-modal="true" aria-labelledby="visual-details-title">
      <button className="dialog-close" type="button" onClick={onClose} aria-label="Close">×</button>
      <img className="visual-details-image" src={imageUrl(item)} alt={item.title} />
      <p className="eyebrow muted">FOUND ITEM REPORT · {item.similarity}% APPROXIMATE VISUAL SIMILARITY</p>
      <h2 id="visual-details-title">{item.title}</h2>
      <p className="visual-details-category">{item.category_name || item.category || 'Campus item'}</p>
      <dl className="visual-details-list"><div><dt>Found at</dt><dd>{item.location}</dd></div><div><dt>Date reported</dt><dd>{dateLabel(item.event_date)}</dd></div><div><dt>Status</dt><dd>{item.status?.replaceAll('_', ' ') || 'Unavailable'}</dd></div></dl>
      <p className="visual-details-description">{item.description}</p>
      <p className="visual-results-caveat">Visual similarity is a suggestion, not a guarantee of ownership.</p>
      <button className="form-submit" type="button" onClick={() => onClaim(item)}>That might be mine <span aria-hidden="true">↗</span></button>
    </section>
  </div>
}

export default VisualSearch