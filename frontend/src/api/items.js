import { request, rowsFrom } from './client.js'

export async function getItems(params, token) {
  const query = params.toString()
  const data = await request(`items/${query ? `?${query}` : ''}`, { token })
  return { rows: rowsFrom(data), count: data?.count ?? rowsFrom(data).length }
}

export function createItem(formData, token) {
  return request('items/', { method: 'POST', body: formData, token })
}

export function updateItem(id, formData, token) {
  return request(`items/${id}/`, { method: 'PATCH', body: formData, token })
}

export function deleteItem(id, token) {
  return request(`items/${id}/`, { method: 'DELETE', token })
}

export function searchItemsByImage(formData, token) {
  return request('visual-search/', { method: 'POST', body: formData, token })
}

export function searchFoundItems(params) {
  const query = params.toString()
  return request(`items/search-found/${query ? `?${query}` : ''}`)
}