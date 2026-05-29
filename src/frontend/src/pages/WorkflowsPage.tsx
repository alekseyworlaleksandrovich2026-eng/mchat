import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Eye, Network, Play, Plus, RefreshCw, Settings2, Trash2, Workflow } from 'lucide-react'

import api from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Switch } from '@/components/ui/Switch'
import { Dialog } from '@/components/ui/Dialog'
import { toast } from '@/components/ui/Toast'
import { Spinner } from '@/components/ui/Spinner'
import { WorkflowGraphEditor, type WorkflowGraphValue } from '@/components/workflow/WorkflowGraphEditor'

interface Skill {
  id: string
  name: string
}

interface WorkflowItem {
  id: string
  name: string
  description?: string | null
  enabled: boolean
  created_at: string
  updated_at: string
  graph_json?: WorkflowGraphValue | null
}

interface WorkflowStep {
  id: string
  step_key: string
  name: string
  order_index: number
  skill_id: string
  skill_name: string
  payload_template?: Record<string, unknown> | null
  on_error: 'stop' | 'continue'
  enabled: boolean
}

interface WorkflowStepRun {
  id: string
  step_id: string
  step_key: string
  step_name: string
  skill_id: string
  skill_name: string
  status: string
  payload?: Record<string, unknown> | null
  result?: Record<string, unknown> | null
  error?: string | null
  started_at: string
  finished_at?: string | null
  duration_ms?: number | null
}

interface WorkflowRun {
  id: string
  workflow_id: string
  workflow_name: string
  trigger_type: string
  status: string
  input_payload?: Record<string, unknown> | null
  output_payload?: Record<string, unknown> | null
  error?: string | null
  started_at: string
  finished_at?: string | null
  duration_ms?: number | null
}

interface WorkflowRunDetail extends WorkflowRun {
  step_runs: WorkflowStepRun[]
  node_runs?: Array<{
    node_id: string
    node_type: string
    node_name?: string
    status: string
    payload?: Record<string, unknown> | null
    result?: Record<string, unknown> | null
    error?: string | null
    started_at: string
    finished_at?: string | null
    duration_ms?: number | null
  }>
  pending_approvals?: Array<{
    id: string
    node_id: string
    node_name?: string | null
    status: string
    created_at: string
    comment?: string | null
  }>
  can_resume?: boolean
}

interface WorkflowApprovalTask {
  id: string
  workflow_run_id: string
  workflow_id: string
  workflow_name: string
  node_id: string
  node_name?: string | null
  status: string
  created_at: string
}

export function WorkflowsPage() {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([])
  const [runs, setRuns] = useState<WorkflowRun[]>([])
  const [skills, setSkills] = useState<Skill[]>([])
  const [runningMap, setRunningMap] = useState<Record<string, boolean>>({})
  const [pendingApprovals, setPendingApprovals] = useState<WorkflowApprovalTask[]>([])

  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [stepsOpen, setStepsOpen] = useState(false)
  const [runDetailOpen, setRunDetailOpen] = useState(false)
  const [graphOpen, setGraphOpen] = useState(false)

  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowItem | null>(null)
  const [selectedRunDetail, setSelectedRunDetail] = useState<WorkflowRunDetail | null>(null)
  const [graphDraft, setGraphDraft] = useState<WorkflowGraphValue | null>(null)

  const [nameInput, setNameInput] = useState('')
  const [descriptionInput, setDescriptionInput] = useState('')
  const [enabledInput, setEnabledInput] = useState(true)
  const [saving, setSaving] = useState(false)

  const [stepsJson, setStepsJson] = useState('[]')
  const [savingSteps, setSavingSteps] = useState(false)

  useEffect(() => {
    loadAll()
  }, [])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [workflowData, runData, skillData] = await Promise.all([
        api.get<WorkflowItem[]>('/workflows'),
        api.get<WorkflowRun[]>('/workflows/runs/list', { limit: '40' }),
        api.get<Skill[]>('/skills'),
      ])
      const approvals = await api.get<WorkflowApprovalTask[]>('/workflows/approvals/pending', {
        limit: '50',
      })
      setWorkflows(workflowData)
      setRuns(runData)
      setSkills(skillData)
      setPendingApprovals(approvals)
    } catch (err: any) {
      toast(t('workflows.toastLoadFailed'), { type: 'error', message: err.message })
    } finally {
      setLoading(false)
    }
  }

  const openCreate = () => {
    setNameInput('')
    setDescriptionInput('')
    setEnabledInput(true)
    setCreateOpen(true)
  }

  const openEdit = (row: WorkflowItem) => {
    setSelectedWorkflow(row)
    setNameInput(row.name)
    setDescriptionInput(row.description || '')
    setEnabledInput(row.enabled)
    setEditOpen(true)
  }

  const saveCreate = async () => {
    if (!nameInput.trim()) return
    setSaving(true)
    try {
      await api.post('/workflows', {
        name: nameInput.trim(),
        description: descriptionInput.trim() || null,
        enabled: enabledInput,
      })
      setCreateOpen(false)
      await loadAll()
      toast(t('workflows.toastCreated'), { type: 'success' })
    } catch (err: any) {
      toast(t('workflows.toastSaveFailed'), { type: 'error', message: err.message })
    } finally {
      setSaving(false)
    }
  }

  const saveEdit = async () => {
    if (!selectedWorkflow) return
    setSaving(true)
    try {
      await api.patch(`/workflows/${selectedWorkflow.id}`, {
        name: nameInput.trim(),
        description: descriptionInput.trim() || null,
        enabled: enabledInput,
      })
      setEditOpen(false)
      await loadAll()
      toast(t('workflows.toastUpdated'), { type: 'success' })
    } catch (err: any) {
      toast(t('workflows.toastSaveFailed'), { type: 'error', message: err.message })
    } finally {
      setSaving(false)
    }
  }

  const toggleWorkflow = async (row: WorkflowItem, enabled: boolean) => {
    try {
      await api.patch(`/workflows/${row.id}`, { enabled })
      setWorkflows((prev) => prev.map((x) => (x.id === row.id ? { ...x, enabled } : x)))
    } catch (err: any) {
      toast(t('workflows.toastSaveFailed'), { type: 'error', message: err.message })
    }
  }

  const deleteWorkflow = async (row: WorkflowItem) => {
    if (!window.confirm(t('workflows.deleteConfirm', { name: row.name }))) return
    try {
      await api.delete(`/workflows/${row.id}`)
      setWorkflows((prev) => prev.filter((x) => x.id !== row.id))
      toast(t('workflows.toastDeleted'), { type: 'success' })
    } catch (err: any) {
      toast(t('workflows.toastDeleteFailed'), { type: 'error', message: err.message })
    }
  }

  const runOnce = async (row: WorkflowItem) => {
    setRunningMap((prev) => ({ ...prev, [row.id]: true }))
    try {
      await api.post(`/workflows/${row.id}/run-once`, { payload: {} })
      toast(t('workflows.toastRunTriggered'), { type: 'success' })
      await loadAll()
    } catch (err: any) {
      toast(t('workflows.toastRunFailed'), { type: 'error', message: err.message })
    } finally {
      setRunningMap((prev) => ({ ...prev, [row.id]: false }))
    }
  }

  const openStepsEditor = async (row: WorkflowItem) => {
    setSelectedWorkflow(row)
    try {
      const steps = await api.get<WorkflowStep[]>(`/workflows/${row.id}/steps`)
      setStepsJson(JSON.stringify(steps.map((s) => ({
        step_key: s.step_key,
        name: s.name,
        order_index: s.order_index,
        skill_id: s.skill_id,
        payload_template: s.payload_template || {},
        on_error: s.on_error,
        enabled: s.enabled,
      })), null, 2))
      setStepsOpen(true)
    } catch (err: any) {
      toast(t('workflows.toastLoadStepsFailed'), { type: 'error', message: err.message })
    }
  }

  const openGraphEditor = (row: WorkflowItem) => {
    setSelectedWorkflow(row)
    setGraphDraft(row.graph_json || { version: 1, nodes: [], edges: [] })
    setGraphOpen(true)
  }

  const saveGraph = async (graph: WorkflowGraphValue) => {
    if (!selectedWorkflow) return
    try {
      await api.patch(`/workflows/${selectedWorkflow.id}`, { graph_json: graph })
      toast(t('workflows.toastGraphSaved'), { type: 'success' })
      setGraphOpen(false)
      await loadAll()
    } catch (err: any) {
      toast(t('workflows.toastGraphSaveFailed'), { type: 'error', message: err.message })
    }
  }

  const saveSteps = async () => {
    if (!selectedWorkflow) return
    let parsed: unknown
    try {
      parsed = JSON.parse(stepsJson)
    } catch {
      toast(t('workflows.toastInvalidStepsJson'), { type: 'error' })
      return
    }
    if (!Array.isArray(parsed)) {
      toast(t('workflows.toastInvalidStepsJson'), { type: 'error' })
      return
    }
    setSavingSteps(true)
    try {
      await api.put(`/workflows/${selectedWorkflow.id}/steps`, { steps: parsed })
      setStepsOpen(false)
      toast(t('workflows.toastStepsSaved'), { type: 'success' })
    } catch (err: any) {
      toast(t('workflows.toastSaveStepsFailed'), { type: 'error', message: err.message })
    } finally {
      setSavingSteps(false)
    }
  }

  const openRunDetail = async (run: WorkflowRun) => {
    try {
      const detail = await api.get<WorkflowRunDetail>(`/workflows/runs/${run.id}`)
      setSelectedRunDetail(detail)
      setRunDetailOpen(true)
    } catch (err: any) {
      toast(t('workflows.toastLoadRunDetailFailed'), { type: 'error', message: err.message })
    }
  }

  const approveTask = async (task: WorkflowApprovalTask) => {
    try {
      await api.post(`/workflows/approvals/${task.id}/approve`, {
        comment: null,
        auto_resume: true,
        decision_payload: {},
      })
      toast(t('workflows.toastApprovalApproved'), { type: 'success' })
      await loadAll()
    } catch (err: any) {
      toast(t('workflows.toastApprovalActionFailed'), { type: 'error', message: err.message })
    }
  }

  const rejectTask = async (task: WorkflowApprovalTask) => {
    const comment = window.prompt(t('workflows.approvalRejectPrompt')) || ''
    try {
      await api.post(`/workflows/approvals/${task.id}/reject`, {
        comment,
        auto_resume: false,
        decision_payload: {},
      })
      toast(t('workflows.toastApprovalRejected'), { type: 'success' })
      await loadAll()
    } catch (err: any) {
      toast(t('workflows.toastApprovalActionFailed'), { type: 'error', message: err.message })
    }
  }

  const resumeRun = async (runId: string) => {
    try {
      await api.post(`/workflows/runs/${runId}/resume`, { payload: {} })
      toast(t('workflows.toastRunResumed'), { type: 'success' })
      await loadAll()
    } catch (err: any) {
      toast(t('workflows.toastResumeFailed'), { type: 'error', message: err.message })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="md" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            {t('workflows.pageTitle')}
            <Badge variant="warning">{t('common.beta')}</Badge>
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t('workflows.pageSubtitle')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" leftIcon={<RefreshCw className="w-4 h-4" />} onClick={loadAll}>
            {t('common.refresh')}
          </Button>
          <Button leftIcon={<Plus className="w-4 h-4" />} onClick={openCreate}>
            {t('workflows.newWorkflow')}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>{t('workflows.listTitle')}</CardHeader>
        <CardContent className="p-0">
          {workflows.length === 0 ? (
            <div className="py-14 text-center text-gray-500 dark:text-gray-400">
              <Workflow className="w-10 h-10 mx-auto mb-2 opacity-60" />
              {t('workflows.empty')}
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {workflows.map((row) => (
                <div key={row.id} className="px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{row.name}</p>
                      <Badge variant={row.enabled ? 'success' : 'default'}>
                        {row.enabled ? t('common.enabled') : t('common.disabled')}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {row.description || t('workflows.noDescription')}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {t('workflows.updatedAt')}: {formatDate(row.updated_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Switch checked={row.enabled} onChange={(v) => toggleWorkflow(row, v)} />
                    <Button
                      size="sm"
                      variant="secondary"
                      leftIcon={<Play className="w-4 h-4" />}
                      isLoading={!!runningMap[row.id]}
                      onClick={() => runOnce(row)}
                    >
                      {t('workflows.runOnce')}
                    </Button>
                    <Button size="sm" variant="outline" leftIcon={<Settings2 className="w-4 h-4" />} onClick={() => openStepsEditor(row)}>
                      {t('workflows.editSteps')}
                    </Button>
                    <Button size="sm" variant="outline" leftIcon={<Network className="w-4 h-4" />} onClick={() => openGraphEditor(row)}>
                      {t('workflows.editGraph')}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => openEdit(row)}>
                      {t('common.edit')}
                    </Button>
                    <Button size="sm" variant="danger" leftIcon={<Trash2 className="w-4 h-4" />} onClick={() => deleteWorkflow(row)}>
                      {t('common.delete')}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>{t('workflows.approvalsTitle')}</CardHeader>
        <CardContent className="p-0">
          {pendingApprovals.length === 0 ? (
            <div className="py-8 text-center text-gray-500 dark:text-gray-400">
              {t('workflows.approvalsEmpty')}
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {pendingApprovals.map((task) => (
                <div key={task.id} className="px-6 py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {task.workflow_name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {task.node_name || task.node_id} · {formatDate(task.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button size="sm" variant="secondary" onClick={() => approveTask(task)}>
                      {t('workflows.approve')}
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => rejectTask(task)}>
                      {t('workflows.reject')}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>{t('workflows.runsTitle')}</CardHeader>
        <CardContent className="p-0">
          {runs.length === 0 ? (
            <div className="py-10 text-center text-gray-500 dark:text-gray-400">
              {t('workflows.noRuns')}
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {runs.map((run) => (
                <div key={run.id} className="px-6 py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {run.workflow_name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {formatDate(run.started_at)} · {run.trigger_type}
                      {run.error ? ` · ${run.error}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge
                      variant={
                        run.status === 'success'
                          ? 'success'
                          : run.status === 'failed'
                            ? 'danger'
                            : run.status === 'paused'
                              ? 'warning'
                              : 'default'
                      }
                    >
                      {run.status}
                    </Badge>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {run.duration_ms != null ? `${run.duration_ms}ms` : '-'}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      leftIcon={<Eye className="w-4 h-4" />}
                      onClick={() => openRunDetail(run)}
                    >
                      {t('workflows.viewDetail')}
                    </Button>
                    {run.status === 'paused' ? (
                      <Button size="sm" variant="secondary" onClick={() => resumeRun(run.id)}>
                        {t('workflows.resumeRun')}
                      </Button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title={t('workflows.createDialogTitle')} size="md">
        <div className="space-y-4">
          <Input label={t('workflows.formName')} value={nameInput} onChange={(e) => setNameInput(e.target.value)} />
          <Input label={t('workflows.formDescription')} value={descriptionInput} onChange={(e) => setDescriptionInput(e.target.value)} />
          <Switch checked={enabledInput} onChange={setEnabledInput} label={t('workflows.formEnabled')} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={saveCreate} isLoading={saving} disabled={!nameInput.trim()}>{t('common.create')}</Button>
          </div>
        </div>
      </Dialog>

      <Dialog open={editOpen} onClose={() => setEditOpen(false)} title={t('workflows.editDialogTitle')} size="md">
        <div className="space-y-4">
          <Input label={t('workflows.formName')} value={nameInput} onChange={(e) => setNameInput(e.target.value)} />
          <Input label={t('workflows.formDescription')} value={descriptionInput} onChange={(e) => setDescriptionInput(e.target.value)} />
          <Switch checked={enabledInput} onChange={setEnabledInput} label={t('workflows.formEnabled')} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEditOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={saveEdit} isLoading={saving} disabled={!nameInput.trim()}>{t('common.save')}</Button>
          </div>
        </div>
      </Dialog>

      <Dialog open={stepsOpen} onClose={() => setStepsOpen(false)} title={t('workflows.stepsDialogTitle')} size="xl">
        <div className="space-y-3">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t('workflows.stepsHint')}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t('workflows.availableSkills')}: {skills.map((s) => s.name).join(', ') || '-'}
          </p>
          <textarea
            className="w-full h-96 text-xs font-mono rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 p-3"
            value={stepsJson}
            onChange={(e) => setStepsJson(e.target.value)}
          />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setStepsOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={saveSteps} isLoading={savingSteps}>{t('common.save')}</Button>
          </div>
        </div>
      </Dialog>

      <Dialog open={runDetailOpen} onClose={() => setRunDetailOpen(false)} title={t('workflows.runDetailTitle')} size="xl">
        {selectedRunDetail && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
              <p className="text-gray-600 dark:text-gray-300"><span className="font-medium">{t('workflows.detailWorkflow')}:</span> {selectedRunDetail.workflow_name}</p>
              <p className="text-gray-600 dark:text-gray-300"><span className="font-medium">{t('workflows.detailStatus')}:</span> {selectedRunDetail.status}</p>
              <p className="text-gray-600 dark:text-gray-300"><span className="font-medium">{t('workflows.detailTriggerType')}:</span> {selectedRunDetail.trigger_type}</p>
              <p className="text-gray-600 dark:text-gray-300"><span className="font-medium">{t('workflows.detailDuration')}:</span> {selectedRunDetail.duration_ms != null ? `${selectedRunDetail.duration_ms}ms` : '-'}</p>
            </div>
            {selectedRunDetail.pending_approvals && selectedRunDetail.pending_approvals.length > 0 ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800 p-3">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-2">
                  {t('workflows.pendingApprovalHint')}
                </p>
                <div className="space-y-1">
                  {selectedRunDetail.pending_approvals.map((a) => (
                    <p key={a.id} className="text-xs text-amber-800 dark:text-amber-200">
                      - {a.node_name || a.node_id} · {formatDate(a.created_at)}
                    </p>
                  ))}
                </div>
              </div>
            ) : null}
            {selectedRunDetail.can_resume ? (
              <div className="flex justify-end">
                <Button size="sm" variant="secondary" onClick={() => resumeRun(selectedRunDetail.id)}>
                  {t('workflows.resumeRun')}
                </Button>
              </div>
            ) : null}

            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{t('workflows.detailStepRuns')}</p>
              <div className="space-y-2 max-h-80 overflow-auto pr-1">
                {selectedRunDetail.step_runs.map((step) => (
                  <div key={step.id} className="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {step.step_name} · {step.skill_name}
                      </p>
                      <Badge
                        variant={step.status === 'success' ? 'success' : step.status === 'failed' ? 'danger' : 'warning'}
                      >
                        {step.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {formatDate(step.started_at)} · {step.duration_ms != null ? `${step.duration_ms}ms` : '-'}
                    </p>
                    {step.error ? (
                      <pre className="text-xs rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-2 mt-2 text-red-800 dark:text-red-200 overflow-auto">
{step.error}
                      </pre>
                    ) : null}
                    <details className="mt-2">
                      <summary className="text-xs cursor-pointer text-gray-600 dark:text-gray-300">
                        {t('workflows.viewStepPayloadAndResult')}
                      </summary>
                      <pre className="text-xs rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-2 mt-2 text-gray-800 dark:text-gray-200 overflow-auto">
{JSON.stringify({ payload: step.payload || {}, result: step.result || {} }, null, 2)}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            </div>
            {selectedRunDetail.node_runs && selectedRunDetail.node_runs.length > 0 ? (
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  {t('workflows.detailNodeRuns')}
                </p>
                <div className="space-y-2 max-h-80 overflow-auto pr-1">
                  {selectedRunDetail.node_runs.map((node) => (
                    <div key={`${node.node_id}-${node.started_at}`} className="rounded-lg border border-gray-200 dark:border-gray-700 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {node.node_name || node.node_id} · {node.node_type}
                        </p>
                        <Badge variant={node.status === 'success' ? 'success' : node.status === 'failed' ? 'danger' : 'warning'}>
                          {node.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatDate(node.started_at)} · {node.duration_ms != null ? `${node.duration_ms}ms` : '-'}
                      </p>
                      {node.error ? (
                        <pre className="text-xs rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-2 mt-2 text-red-800 dark:text-red-200 overflow-auto">
{node.error}
                        </pre>
                      ) : null}
                      <details className="mt-2">
                        <summary className="text-xs cursor-pointer text-gray-600 dark:text-gray-300">
                          {t('workflows.viewStepPayloadAndResult')}
                        </summary>
                        <pre className="text-xs rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-2 mt-2 text-gray-800 dark:text-gray-200 overflow-auto">
{JSON.stringify({ payload: node.payload || {}, result: node.result || {} }, null, 2)}
                        </pre>
                      </details>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </Dialog>
      <Dialog
        open={graphOpen}
        onClose={() => setGraphOpen(false)}
        title={t('workflows.graphDialogTitle')}
        size="full"
        className="h-[95vh]"
        bodyClassName="flex min-h-0 flex-1 flex-col overflow-hidden p-0"
      >
        {graphDraft && (
          <WorkflowGraphEditor value={graphDraft} skills={skills} onSave={saveGraph} />
        )}
      </Dialog>
    </div>
  )
}
