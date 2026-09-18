import axios from 'axios'

const ACCESS_SESSION_KEY = 'site_access_key'

export function getAccessSession() {
  return localStorage.getItem(ACCESS_SESSION_KEY) || ''
}

export function clearAccessSession() {
  localStorage.removeItem(ACCESS_SESSION_KEY)
}

function isAccessBootstrapRequest(url) {
  return url.endsWith('/access/status') || url.endsWith('/access/verify')
}

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 20000,
})

api.interceptors.request.use((config) => {
  const accessKey = getAccessSession()
  if (accessKey) {
    config.headers = config.headers || {}
    config.headers['X-Access-Key'] = accessKey
  }
  return config
})

api.interceptors.response.use(
  (response) => {
    const requestUrl = String(response?.config?.url || '')
    if (
      isAccessBootstrapRequest(requestUrl) &&
      (response?.data?.authenticated === true || response?.data?.enabled === false)
    ) {
      // New sessions are HttpOnly cookies. Drop only the legacy localStorage
      // copy after the backend has confirmed the session/bootstrap state.
      clearAccessSession()
    }
    return response
  },
  (error) => {
    const requestUrl = String(error?.config?.url || '')
    if (error?.response?.status === 401 && !isAccessBootstrapRequest(requestUrl)) {
      clearAccessSession()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('site-access-required'))
      }
    }
    return Promise.reject(error)
  },
)

export default api
