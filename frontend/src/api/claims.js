import { request } from './client.js'

export function createClaim(claim, token) {
  return request('claims/', { method: 'POST', body: JSON.stringify(claim), token })
}

export function decideClaim(id, status, reason, token) {
  return request(`claims/${id}/decision/`, { method: 'PATCH', body: JSON.stringify({ status, reason }), token })
}