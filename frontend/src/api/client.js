const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export async function request(path, { token, ...options } = {}) {
  const headers = new Headers(options.headers || {})
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_URL}/${path.replace(/^\//, '')}`, { ...options, headers })
  const data = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    const message = data?.detail || Object.values(data || {}).flat().find((value) => typeof value === 'string') || 'The request could not be completed.'
    throw new Error(message)
  }
  return data
}

export function rowsFrom(data) {
  return Array.isArray(data) ? data : data?.results || []
}