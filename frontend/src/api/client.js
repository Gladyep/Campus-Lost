const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const authStorageKey = 'campusconnect.auth'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function readStoredAuth() {
  try {
    return JSON.parse(localStorage.getItem(authStorageKey) || 'null')
  } catch {
    return null
  }
}

async function send(path, options, token) {
  const headers = new Headers(options.headers || {})
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  let response
  try {
    response = await fetch(`${API_URL}/${path.replace(/^\//, '')}`, { ...options, headers })
  } catch {
    throw new ApiError('Unable to reach the CampusConnect API. Check that the backend is running.', 0)
  }
  const data = response.status === 204 ? null : await response.json().catch(() => null)
  return { response, data }
}

function errorFrom(data, status) {
  const message = data?.detail || Object.values(data || {}).flat(Infinity).find((value) => typeof value === 'string') || 'The request could not be completed.'
  return new ApiError(message, status)
}

export async function request(path, { token, ...options } = {}) {
  const storedAuth = token ? readStoredAuth() : null
  let accessToken = storedAuth?.access || token
  let result = await send(path, options, accessToken)

  if (result.response.status === 401 && storedAuth?.refresh && path !== 'auth/refresh/') {
    try {
      const refreshed = await send('auth/refresh/', {
        method: 'POST',
        body: JSON.stringify({ refresh: storedAuth.refresh }),
      })
      if (refreshed.response.ok && refreshed.data?.access) {
        accessToken = refreshed.data.access
        localStorage.setItem(authStorageKey, JSON.stringify({ ...storedAuth, access: accessToken, refresh: refreshed.data.refresh || storedAuth.refresh }))
        result = await send(path, options, accessToken)
      }
    } catch {
      // Keep the original response so callers can distinguish expired auth from an API outage.
    }
  }

  if (!result.response.ok) throw errorFrom(result.data, result.response.status)
  return result.data
}

export function rowsFrom(data) {
  return Array.isArray(data) ? data : data?.results || []
}