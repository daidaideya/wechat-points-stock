import axios from 'axios'

const ACCESS_SESSION_KEY = 'site_access_key'

export function getAccessSession() {
  return localStorage.getItem(ACCESS_SESSION_KEY) || ''
}

export function setAccessSession(value) {
  if (!value) {
    localStorage.removeItem(ACCESS_SESSION_KEY)
    return
  }
  localStorage.setItem(ACCESS_SESSION_KEY, value)
}

export function clearAccessSession() {
  localStorage.removeItem(ACCESS_SESSION_KEY)
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 20000,
})

api.interceptors.request.use((config) => {
  const accessKey = getAccessSession()
  if (accessKey) {
    config.headers['X-Access-Key'] = accessKey
  }
  return config
})

export default api
