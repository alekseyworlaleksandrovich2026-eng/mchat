import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Eye, EyeOff, Edit3, Plus, Trash2 } from 'lucide-react'
import api from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'

interface Template {
  id: string
  name: string
  description: string | null
  category: string
  icon: string | null
  price_monthly_cents: number
  price_yearly_cents: number
  trial_days: number
  is_published: boolean
  sort_order: number
  default_ai_config_spec: any
  default_skill_ids: string[] | null
  default_knowledge_base_spec: any
  default_theme: any
  default_welcome_message: string | null
  default_offline_message: string | null
  created_at: string
  updated_at: string
}

export function TemplateManager() {
  const { t } = useTranslation()
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Template | null>(null)
  const [creating, setCreating] = useState(false)
  const [saving, setSaving] = useState(false)

  const [form, setForm] = useState({
    name: '', description: '', category: 'customer_service', icon: '',
    price_monthly_cents: 0, price_yearly_cents: 0, trial_days: 14,
    is_published: false, sort_order: 0,
    default_welcome_message: '', default_offline_message: '',
    default_ai_config_spec: '{}',
    default_theme: '{}',
  })

  const load = async () => {
    setLoading(true)
    try {
      const data = await api.get<Template[]>('/admin/templates')
      setTemplates(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const openEdit = (tmpl: Template) => {
    setEditing(tmpl)
    setCreating(false)
    setForm({
      name: tmpl.name,
      description: tmpl.description || '',
      category: tmpl.category,
      icon: tmpl.icon || '',
      price_monthly_cents: tmpl.price_monthly_cents,
      price_yearly_cents: tmpl.price_yearly_cents,
      trial_days: tmpl.trial_days,
      is_published: tmpl.is_published,
      sort_order: tmpl.sort_order,
      default_welcome_message: tmpl.default_welcome_message || '',
      default_offline_message: tmpl.default_offline_message || '',
      default_ai_config_spec: JSON.stringify(tmpl.default_ai_config_spec || {}, null, 2),
      default_theme: JSON.stringify(tmpl.default_theme || {}, null, 2),
    })
  }

  const openCreate = () => {
    setEditing(null)
    setCreating(true)
    setForm({
      name: '', description: '', category: 'customer_service', icon: '',
      price_monthly_cents: 0, price_yearly_cents: 0, trial_days: 14,
      is_published: false, sort_order: 0,
      default_welcome_message: '', default_offline_message: '',
      default_ai_config_spec: '{}', default_theme: '{}',
    })
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      let parsedAi: any = {}
      let parsedTheme: any = {}
      try { parsedAi = JSON.parse(form.default_ai_config_spec) } catch {}
      try { parsedTheme = JSON.parse(form.default_theme) } catch {}

      const payload = {
        ...form,
        price_monthly_cents: Number(form.price_monthly_cents),
        price_yearly_cents: Number(form.price_yearly_cents),
        trial_days: Number(form.trial_days),
        sort_order: Number(form.sort_order),
        default_ai_config_spec: parsedAi,
        default_theme: parsedTheme,
      }

      if (editing) {
        await api.put(`/admin/templates/${editing.id}`, payload)
      } else {
        await api.post('/admin/templates', payload)
      }
      setEditing(null)
      setCreating(false)
      load()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this template?')) return
    try {
      await api.delete(`/admin/templates/${id}`)
      load()
    } catch (e: any) {
      setError(e.message)
    }
  }

  const handleTogglePublish = async (tmpl: Template) => {
    try {
      await api.put(`/admin/templates/${tmpl.id}`, { is_published: !tmpl.is_published })
      load()
    } catch (e: any) {
      setError(e.message)
    }
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>

  return (
    <div className="space-y-4">
      {error && <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">{error}</div>}

      <div className="flex justify-between items-center">
        <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
          Templates ({templates.length})
        </h2>
        <Button onClick={openCreate} size="sm"><Plus className="w-4 h-4 mr-1" />New Template</Button>
      </div>

      {/* List */}
      <div className="space-y-2">
        {templates.map((tmpl) => (
          <div key={tmpl.id} className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">{tmpl.name}</span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500">{tmpl.category}</span>
                {tmpl.is_published
                  ? <Eye className="w-3.5 h-3.5 text-green-500" />
                  : <EyeOff className="w-3.5 h-3.5 text-gray-400" />}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                ¥{(tmpl.price_monthly_cents / 100).toFixed(0)}/mo · {tmpl.trial_days}d trial · sort {tmpl.sort_order}
              </div>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button onClick={() => handleTogglePublish(tmpl)} className="p-1.5 text-gray-400 hover:text-primary-500 rounded" title={tmpl.is_published ? 'Unpublish' : 'Publish'}>
                {tmpl.is_published ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
              <button onClick={() => openEdit(tmpl)} className="p-1.5 text-gray-400 hover:text-primary-500 rounded"><Edit3 className="w-4 h-4" /></button>
              <button onClick={() => handleDelete(tmpl.id)} className="p-1.5 text-gray-400 hover:text-red-500 rounded"><Trash2 className="w-4 h-4" /></button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit / Create modal */}
      {(editing || creating) && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-start justify-center pt-10 px-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto p-6 space-y-4">
            <h3 className="text-lg font-semibold">{creating ? 'New Template' : `Edit: ${editing?.name}`}</h3>
            <Input label="Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Category" value={form.category} onChange={e => setForm({...form, category: e.target.value})} />
              <Input label="Icon (lucide)" value={form.icon} onChange={e => setForm({...form, icon: e.target.value})} />
              <Input label="Price (cents/mo)" type="number" value={String(form.price_monthly_cents)} onChange={e => setForm({...form, price_monthly_cents: Number(e.target.value)})} />
              <Input label="Trial days" type="number" value={String(form.trial_days)} onChange={e => setForm({...form, trial_days: Number(e.target.value)})} />
              <Input label="Sort order" type="number" value={String(form.sort_order)} onChange={e => setForm({...form, sort_order: Number(e.target.value)})} />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_published} onChange={e => setForm({...form, is_published: e.target.checked})} />
              Published (visible in marketplace)
            </label>
            <Input label="Welcome message" value={form.default_welcome_message} onChange={e => setForm({...form, default_welcome_message: e.target.value})} />
            <div>
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Description</label>
              <textarea className="w-full mt-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 p-2 text-sm" rows={2}
                value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">AI Config Spec (JSON)</label>
              <textarea className="w-full mt-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 p-2 text-xs font-mono" rows={4}
                value={form.default_ai_config_spec} onChange={e => setForm({...form, default_ai_config_spec: e.target.value})} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Theme (JSON)</label>
              <textarea className="w-full mt-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 p-2 text-xs font-mono" rows={3}
                value={form.default_theme} onChange={e => setForm({...form, default_theme: e.target.value})} />
            </div>
            <div className="flex gap-2 justify-end pt-2">
              <Button variant="outline" onClick={() => { setEditing(null); setCreating(false) }}>Cancel</Button>
              <Button onClick={handleSave} isLoading={saving}>Save</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
