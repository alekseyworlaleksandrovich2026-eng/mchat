const API_BASE = '/api'

interface RequestOptions extends RequestInit {
  params?: Record<string, string>
}

class ApiError extends Error {
  status: number
  data: any

  constructor(message: string, status: number, data?: any) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function getToken(): string | null {
  return localStorage.getItem('mchat_token')
}

function setToken(token: string): void {
  localStorage.setItem('mchat_token', token)
}

function removeToken(): void {
  localStorage.removeItem('mchat_token')
}

async function request<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options

  let url = `${API_BASE}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams(params)
    url += `?${searchParams.toString()}`
  }

  const isFormData = options.body instanceof FormData
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers as Record<string, string>),
  }

  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  })

  if (!response.ok) {
    let errorData: any
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: response.statusText }
    }

    if (response.status === 401) {
      const isLoginRequest = endpoint === '/auth/login'
      if (!isLoginRequest) {
        removeToken()
        if (window.location.pathname !== '/admin/login') {
          window.location.href = '/admin/login'
        }
      }
    }

    const detail =
      errorData.detail ??
      errorData.message ??
      errorData.error ??
      (typeof errorData === 'string' ? errorData : null)

    throw new ApiError(
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || String(d)).join('; ')
          : '请求失败',
      response.status,
      errorData,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const api = {
  get: <T = any>(endpoint: string, params?: Record<string, string>) =>
    request<T>(endpoint, { method: 'GET', params }),

  post: <T = any>(endpoint: string, data?: any) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),

  put: <T = any>(endpoint: string, data?: any) =>
    request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),

  patch: <T = any>(endpoint: string, data?: any) =>
    request<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),

  delete: <T = any>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' }),

  upload: <T = any>(endpoint: string, formData: FormData) =>
    request<T>(endpoint, {
      method: 'POST',
      body: formData,
    }),
}

export { setToken, removeToken, getToken, ApiError }
export default api
