import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'

export function useAuth(requireAuth: boolean = true) {
  const { isAuthenticated, isLoading, user, checkAuth, login, logout, error, clearError } =
    useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  useEffect(() => {
    if (!isLoading && requireAuth && !isAuthenticated) {
      navigate('/admin/login')
    }
  }, [isLoading, requireAuth, isAuthenticated, navigate])

  return {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    error,
    clearError,
  }
}
