import { create } from 'zustand'
import api, { setToken, removeToken } from '@/lib/api'

export interface User {
  id: string
  username: string
  role: 'admin' | 'agent'
  display_name?: string | null
  avatar_url?: string | null
  email?: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  login: (username: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('mchat_token'),
  isLoading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post<{ access_token: string; token_type: string; user: User }>('/auth/login', {
        username,
        password,
      })
      setToken(res.access_token)
      set({
        user: res.user,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.message || '登录失败',
      })
      throw err
    }
  },

  logout: () => {
    removeToken()
    set({
      user: null,
      isAuthenticated: false,
    })
  },

  checkAuth: async () => {
    const token = localStorage.getItem('mchat_token')
    if (!token) {
      set({ isAuthenticated: false, user: null })
      return
    }
    set({ isLoading: true })
    try {
      const user = await api.get<User>('/auth/me')
      set({ user, isAuthenticated: true, isLoading: false })
    } catch {
      removeToken()
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },

  clearError: () => set({ error: null }),
}))
