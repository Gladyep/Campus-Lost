import { request, rowsFrom } from './client.js'

export async function getResource(path, token) {
  const data = await request(path, { token })
  return Array.isArray(data) || data?.results ? rowsFrom(data) : data
}

export async function getResourceCount(path, token) {
  const data = await request(path, { token })
  return data?.count ?? rowsFrom(data).length
}

export async function getNotifications(params, token) {
  const query = params.toString()
  const data = await request(`notifications/${query ? `?${query}` : ''}`, { token })
  return { rows: rowsFrom(data), count: data?.count ?? 0, next: data?.next || null, previous: data?.previous || null }
}

export async function getUnreadNotificationCount(token) {
  return request('notifications/unread-count/', { token })
}

export function markNotificationRead(id, token) {
  return request(`notifications/${id}/read/`, { method: 'PATCH', body: JSON.stringify({}), token })
}

export function markAllNotificationsRead(token) {
  return request('notifications/read-all/', { method: 'PATCH', body: JSON.stringify({}), token })
}

export function deleteNotification(id, token) {
  return request(`notifications/${id}/`, { method: 'DELETE', token })
}

export function clearReadNotifications(token) {
  return request('notifications/clear-read/', { method: 'DELETE', token })
}

export function decideReport(id, status, reason, token) {
  return request(`admin/reports/${id}/decision/`, { method: 'POST', body: JSON.stringify({ status, reason }), token })
}