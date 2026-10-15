import { request } from './client.js'

export function login(credentials) {
  return request('auth/login/', { method: 'POST', body: JSON.stringify(credentials) })
}

export function register(details) {
  return request('auth/register/', { method: 'POST', body: JSON.stringify(details) })
}