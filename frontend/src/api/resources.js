import { request, rowsFrom } from './client.js'

export async function getResource(path, token) {
  const data = await request(path, { token })
  return Array.isArray(data) || data?.results ? rowsFrom(data) : data
}

export async function getResourceCount(path, token) {
  const data = await request(path, { token })
  return data?.count ?? rowsFrom(data).length
}

export function markNotificationRead(id, token) {
  return request(`notifications/${id}/`, { method: 'PATCH', body: JSON.stringify({ is_read: true }), token })
}

export function decideReport(id, status, reason, token) {
  return request(`admin/reports/${id}/decision/`, { method: 'POST', body: JSON.stringify({ status, reason }), token })
}