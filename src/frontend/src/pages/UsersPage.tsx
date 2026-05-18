import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Trash2, UserPlus } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'
import { toast } from '@/components/ui/Toast'
import { ChangePasswordForm } from '@/components/admin/ChangePasswordForm'
import { formatDate } from '@/lib/utils'

interface UserRow {
  id: string
  username: string
  role: 'admin' | 'agent'
  display_name: string | null
  created_at: string
}

export function UsersPage() {
  const { t } = useTranslation()
  const currentUser = useAuthStore((s) => s.user)
  const [users, setUsers] = useState<UserRow[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({
    username: '',
    password: '',
    role: 'agent',
    display_name: '',
  })

  const loadUsers = async () => {
    try {
      const data = await api.get<UserRow[]>('/auth/users')
      setUsers(data)
    } catch (err) {
      console.error(err)
      toast(t('users.loadFailed'), { type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    try {
      await api.post('/auth/users', {
        username: form.username,
        password: form.password,
        role: form.role,
        display_name: form.display_name || form.username,
      })
      toast(t('users.created'), { type: 'success' })
      setForm({ username: '', password: '', role: 'agent', display_name: '' })
      setShowCreate(false)
      await loadUsers()
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : t('users.createFailed'), {
        type: 'error',
      })
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (user: UserRow) => {
    if (!window.confirm(t('users.deleteConfirm', { name: user.username }))) return
    try {
      await api.delete(`/auth/users/${user.id}`)
      toast(t('users.deleted'), { type: 'success' })
      await loadUsers()
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : t('users.deleteFailed'), {
        type: 'error',
      })
    }
  }

  const handleRoleChange = async (user: UserRow, role: string) => {
    try {
      await api.patch(`/auth/users/${user.id}`, { role })
      toast(t('users.updated'), { type: 'success' })
      await loadUsers()
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : t('users.updateFailed'), {
        type: 'error',
      })
    }
  }

  if (currentUser?.role !== 'admin') {
    return (
      <div className="text-center py-20 text-gray-500 dark:text-gray-400">{t('users.adminOnly')}</div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t('users.title')}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t('users.subtitle')}
          </p>
        </div>
        <Button
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setShowCreate((v) => !v)}
        >
          {t('users.createUser')}
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-gray-900 dark:text-gray-100 font-medium">
              <UserPlus className="w-5 h-5" />
              {t('users.createUser')}
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2 max-w-2xl">
              <Input
                label={t('auth.username')}
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                pattern="[a-zA-Z0-9_]+"
                required
              />
              <Input
                label={t('users.displayName')}
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              />
              <Input
                label={t('auth.password')}
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                minLength={6}
                required
              />
              <Select
                label={t('users.role')}
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                options={[
                  { value: 'agent', label: t('users.roleAgent') },
                  { value: 'admin', label: t('users.roleAdmin') },
                ]}
              />
              <div className="sm:col-span-2 flex gap-2">
                <Button type="submit" isLoading={creating}>
                  {t('users.createUser')}
                </Button>
                <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>
                  {t('users.cancel')}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>{t('users.listTitle')}</CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : users.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-6">{t('users.empty')}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700 text-left text-gray-500 dark:text-gray-400">
                    <th className="py-2 pr-4">{t('auth.username')}</th>
                    <th className="py-2 pr-4">{t('users.displayName')}</th>
                    <th className="py-2 pr-4">{t('users.role')}</th>
                    <th className="py-2 pr-4">{t('users.createdAt')}</th>
                    <th className="py-2">{t('users.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr
                      key={user.id}
                      className="border-b border-gray-100 dark:border-gray-800"
                    >
                      <td className="py-3 pr-4 font-medium text-gray-900 dark:text-gray-100">
                        {user.username}
                        {user.id === currentUser?.id && (
                          <Badge variant="info" size="sm" className="ml-2">
                            {t('users.you')}
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 pr-4 text-gray-600 dark:text-gray-400">
                        {user.display_name || '—'}
                      </td>
                      <td className="py-3 pr-4">
                        <Select
                          value={user.role}
                          onChange={(e) => handleRoleChange(user, e.target.value)}
                          disabled={user.id === currentUser?.id}
                          options={[
                            { value: 'agent', label: t('users.roleAgent') },
                            { value: 'admin', label: t('users.roleAdmin') },
                          ]}
                        />
                      </td>
                      <td className="py-3 pr-4 text-gray-500 dark:text-gray-400">
                        {formatDate(user.created_at)}
                      </td>
                      <td className="py-3">
                        <button
                          type="button"
                          disabled={user.id === currentUser?.id}
                          onClick={() => handleDelete(user)}
                          className="p-2 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
                          title={t('users.delete')}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>{t('users.changePassword')}</CardHeader>
        <CardContent>
          <ChangePasswordForm />
        </CardContent>
      </Card>
    </div>
  )
}
