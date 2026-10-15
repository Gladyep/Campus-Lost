import { request, rowsFrom } from './client.js'

export async function getItems(params, token) {
  const query = params.toString()
  const data = await request(`items/${query ? `?${query}` : ''}`, { token })
  return { rows: rowsFrom(data), count: data?.count ?? rowsFrom(data).length }
}

export function createItem(formData, token) {
  return request('items/', { method: 'POST', body: formData, token })
}

export function searchItemsByImage(formData, token) {
  return request('visual-search/', { method: 'POST', body: formData, token })
}