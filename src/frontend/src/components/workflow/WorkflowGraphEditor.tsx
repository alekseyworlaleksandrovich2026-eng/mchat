import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Maximize2,
  Minimize2,
  PanelLeft,
  PanelRight,
  Save,
  Trash2,
} from 'lucide-react'
import {
  Background,
  Controls,
  ReactFlow,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Tabs, TabPanel } from '@/components/ui/Tabs'
import { cn } from '@/lib/utils'

type GraphNodeType = 'start' | 'skill' | 'condition' | 'end' | 'approval'

type SkillOption = {
  id: string
  name: string
}

export interface WorkflowGraphValue {
  version: number
  nodes: Array<{
    id: string
    type: GraphNodeType
    name?: string
    position?: { x: number; y: number }
    config?: Record<string, unknown>
  }>
  edges: Array<{
    id: string
    source: string
    target: string
    source_handle?: string
    target_handle?: string
    condition?: string
  }>
  viewport?: Record<string, unknown>
}

interface Props {
  value?: WorkflowGraphValue | null
  skills: SkillOption[]
  onSave: (value: WorkflowGraphValue) => void
}

const NODE_COLORS: Record<GraphNodeType, string> = {
  start: '#22c55e',
  skill: '#3b82f6',
  condition: '#f59e0b',
  end: '#a855f7',
  approval: '#ef4444',
}

const NODE_TYPES: GraphNodeType[] = ['start', 'skill', 'condition', 'approval', 'end']

function toFlowNodes(
  nodes: WorkflowGraphValue['nodes'],
  isDark: boolean,
): Node[] {
  return nodes.map((node) => ({
    id: node.id,
    type: 'default',
    position: node.position || { x: 100, y: 100 },
    data: {
      label: node.name || `${node.type}:${node.id}`,
      nodeType: node.type,
      config: node.config || {},
    },
    style: {
      borderRadius: 10,
      border: `2px solid ${NODE_COLORS[node.type]}`,
      padding: 6,
      minWidth: 180,
      background: isDark ? '#111827' : '#ffffff',
      color: isDark ? '#e5e7eb' : '#111827',
    },
  }))
}

function toFlowEdges(edges: WorkflowGraphValue['edges']): Edge[] {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.condition || '',
    sourceHandle: edge.source_handle,
    targetHandle: edge.target_handle,
  }))
}

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

function toSafeInt(value: string, fallback: number) {
  const n = Number(value)
  if (!Number.isFinite(n)) return fallback
  return Math.max(0, Math.floor(n))
}

function IconToolButton({
  title,
  onClick,
  disabled,
  active,
  children,
  className,
}: {
  title: string
  onClick: () => void
  disabled?: boolean
  active?: boolean
  children: React.ReactNode
  className?: string
}) {
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'inline-flex h-8 w-8 items-center justify-center rounded-md border transition-colors',
        'border-gray-200 bg-white text-gray-700 hover:bg-gray-100',
        'dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800',
        'disabled:cursor-not-allowed disabled:opacity-40',
        active && 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-950 dark:text-primary-300',
        className,
      )}
    >
      {children}
    </button>
  )
}

export function WorkflowGraphEditor({ value, skills, onSave }: Props) {
  const { t } = useTranslation()
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [dark, setDark] = useState(isDarkMode())
  const [paletteOpen, setPaletteOpen] = useState(true)
  const [propsOpen, setPropsOpen] = useState(true)
  const [advancedMapOpen, setAdvancedMapOpen] = useState(false)
  const [selectedTab, setSelectedTab] = useState<'visual' | 'json'>('visual')

  useEffect(() => {
    const observer = new MutationObserver(() => setDark(isDarkMode()))
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    })
    return () => observer.disconnect()
  }, [])

  const initial = useMemo<WorkflowGraphValue>(
    () =>
      value || {
        version: 1,
        nodes: [],
        edges: [],
      },
    [value],
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(toFlowNodes(initial.nodes, dark))
  const [edges, setEdges, onEdgesChange] = useEdgesState(toFlowEdges(initial.edges))
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null)
  const [fullScreen, setFullScreen] = useState(false)
  const [jsonDraft, setJsonDraft] = useState('')
  const [jsonError, setJsonError] = useState('')

  useEffect(() => {
    setNodes(toFlowNodes(initial.nodes, dark))
    setEdges(toFlowEdges(initial.edges))
  }, [dark, initial, setEdges, setNodes])

  useEffect(() => {
    const onFullscreenChange = () => {
      setFullScreen(Boolean(document.fullscreenElement))
    }
    document.addEventListener('fullscreenchange', onFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', onFullscreenChange)
  }, [])

  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            id: `e_${params.source}_${params.target}_${Date.now()}`,
          },
          eds,
        ),
      ),
    [setEdges],
  )

  const addNode = (nodeType: GraphNodeType) => {
    const id = `${nodeType}_${Date.now()}`
    const next: Node = {
      id,
      type: 'default',
      position: { x: 120 + nodes.length * 40, y: 100 + nodes.length * 28 },
      data: {
        label: `${nodeType}:${id}`,
        nodeType,
        config: nodeType === 'skill' ? { skill_id: '', payload_template: {} } : {},
      },
      style: {
        borderRadius: 10,
        border: `2px solid ${NODE_COLORS[nodeType]}`,
        padding: 6,
        minWidth: 180,
        background: dark ? '#111827' : '#ffffff',
        color: dark ? '#e5e7eb' : '#111827',
      },
    }
    setNodes((prev) => [...prev, next])
    setSelectedNodeId(id)
    setSelectedEdgeId(null)
    setPropsOpen(true)
  }

  const removeSelected = () => {
    if (selectedNodeId) {
      setNodes((prev) => prev.filter((n) => n.id !== selectedNodeId))
      setEdges((prev) => prev.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId))
      setSelectedNodeId(null)
      return
    }
    if (selectedEdgeId) {
      setEdges((prev) => prev.filter((e) => e.id !== selectedEdgeId))
      setSelectedEdgeId(null)
    }
  }

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || null
  const selectedEdge = edges.find((e) => e.id === selectedEdgeId) || null
  const selectedNodeConfig = ((selectedNode?.data as any)?.config || {}) as Record<string, unknown>
  const selectedNodeType = ((selectedNode?.data as any)?.nodeType || 'skill') as GraphNodeType

  const updateNodeData = (nodeId: string, updater: (data: any) => any) => {
    setNodes((prev) =>
      prev.map((n) => (n.id === nodeId ? { ...n, data: updater(n.data as any) } : n)),
    )
  }

  const updateNodeConfig = (key: string, value: unknown) => {
    if (!selectedNode) return
    updateNodeData(selectedNode.id, (data) => ({
      ...data,
      config: {
        ...(data?.config || {}),
        [key]: value,
      },
    }))
  }

  const toggleFullscreen = async () => {
    const el = containerRef.current
    if (!el) return
    if (document.fullscreenElement) {
      await document.exitFullscreen()
      return
    }
    await el.requestFullscreen()
  }

  const saveGraph = () => {
    const payload: WorkflowGraphValue = {
      version: 1,
      nodes: nodes.map((n) => ({
        id: n.id,
        type: ((n.data as any)?.nodeType || 'skill') as GraphNodeType,
        name: String((n.data as any)?.label || ''),
        position: n.position,
        config: ((n.data as any)?.config || {}) as Record<string, unknown>,
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        source_handle: e.sourceHandle || undefined,
        target_handle: e.targetHandle || undefined,
        condition: (typeof e.label === 'string' && e.label) || undefined,
      })),
    }
    onSave(payload)
  }

  const openJsonEditor = () => {
    setJsonError('')
    if (selectedNode) {
      setJsonDraft(JSON.stringify(selectedNodeConfig || {}, null, 2))
      return
    }
    if (selectedEdge) {
      setJsonDraft(
        JSON.stringify(
          {
            condition: typeof selectedEdge.label === 'string' ? selectedEdge.label : '',
          },
          null,
          2,
        ),
      )
      return
    }
    setJsonDraft('{}')
  }

  const applyJsonDraft = () => {
    try {
      const parsed = JSON.parse(jsonDraft || '{}')
      if (!selectedNode && !selectedEdge) return
      if (selectedNode) {
        updateNodeData(selectedNode.id, (data) => ({
          ...data,
          config: parsed,
        }))
      } else if (selectedEdge) {
        setEdges((prev) =>
          prev.map((e) => (e.id === selectedEdge.id ? { ...e, label: String(parsed.condition || '') } : e)),
        )
      }
      setJsonError('')
    } catch {
      setJsonError(t('workflows.graphJsonInvalid'))
    }
  }

  const nodeTypeLabel = (type: GraphNodeType) => {
    const map: Record<GraphNodeType, string> = {
      start: t('workflows.graphNodeStart'),
      skill: t('workflows.graphNodeSkill'),
      condition: t('workflows.graphNodeCondition'),
      approval: t('workflows.graphNodeApproval'),
      end: t('workflows.graphNodeEnd'),
    }
    return map[type]
  }

  return (
    <div
      ref={containerRef}
      className="flex h-full min-h-0 flex-col bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100"
    >
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-gray-200 px-2 py-1.5 dark:border-gray-800">
        <p className="truncate text-xs font-medium text-gray-600 dark:text-gray-300">
          {t('workflows.graphEditorTitle')}
        </p>
        <div className="flex items-center gap-1">
          <IconToolButton
            title={paletteOpen ? t('workflows.graphHideLeft') : t('workflows.graphShowLeft')}
            onClick={() => setPaletteOpen((v) => !v)}
            active={paletteOpen}
          >
            <PanelLeft className="h-4 w-4" />
          </IconToolButton>
          <IconToolButton
            title={propsOpen ? t('workflows.graphHideRight') : t('workflows.graphShowRight')}
            onClick={() => setPropsOpen((v) => !v)}
            active={propsOpen}
          >
            <PanelRight className="h-4 w-4" />
          </IconToolButton>
          <IconToolButton
            title={fullScreen ? t('workflows.graphExitFullscreen') : t('workflows.graphFullscreen')}
            onClick={toggleFullscreen}
          >
            {fullScreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </IconToolButton>
          <IconToolButton
            title={t('workflows.graphDeleteSelected')}
            onClick={removeSelected}
            disabled={!selectedNodeId && !selectedEdgeId}
            className="text-red-600 dark:text-red-400"
          >
            <Trash2 className="h-4 w-4" />
          </IconToolButton>
          <IconToolButton title={t('workflows.graphSave')} onClick={saveGraph}>
            <Save className="h-4 w-4" />
          </IconToolButton>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        {paletteOpen ? (
          <aside className="flex w-48 shrink-0 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <div className="border-b border-gray-200 px-2 py-1.5 text-xs font-medium dark:border-gray-800">
              {t('workflows.graphNodeLibrary')}
            </div>
            <div className="flex flex-col gap-1 overflow-y-auto p-2">
              {NODE_TYPES.map((nodeType) => (
                <button
                  key={nodeType}
                  type="button"
                  title={nodeTypeLabel(nodeType)}
                  onClick={() => addNode(nodeType)}
                  className="rounded-md border border-gray-200 px-2 py-1.5 text-left text-xs hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
                  style={{ borderLeftWidth: 3, borderLeftColor: NODE_COLORS[nodeType] }}
                >
                  {nodeTypeLabel(nodeType)}
                </button>
              ))}
            </div>
          </aside>
        ) : null}

        <div className="min-h-0 min-w-0 flex-1 bg-white dark:bg-gray-900">
          <ReactFlow
            className="h-full w-full"
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => {
              setSelectedNodeId(node.id)
              setSelectedEdgeId(null)
              setSelectedTab('visual')
              setPropsOpen(true)
            }}
            onEdgeClick={(_, edge) => {
              setSelectedEdgeId(edge.id)
              setSelectedNodeId(null)
              setSelectedTab('visual')
              setPropsOpen(true)
            }}
            fitView
            colorMode={dark ? 'dark' : 'light'}
          >
            <Background />
            <Controls />
          </ReactFlow>
        </div>

        {propsOpen ? (
          <aside className="flex w-72 shrink-0 flex-col border-l border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <div className="border-b border-gray-200 px-2 py-1.5 text-xs font-medium dark:border-gray-800">
              {t('workflows.graphProperties')}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-2">
              {!selectedNode && !selectedEdge ? (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('workflows.graphSelectHint')}
                </p>
              ) : (
                <>
                  <Tabs
                    tabs={[
                      { id: 'visual', label: t('workflows.graphTabVisual') },
                      { id: 'json', label: 'JSON' },
                    ]}
                    activeTab={selectedTab}
                    onChange={(tab) => {
                      const next = tab as 'visual' | 'json'
                      setSelectedTab(next)
                      if (next === 'json') openJsonEditor()
                    }}
                  />

                  <TabPanel id="visual" activeTab={selectedTab}>
                    {selectedNode ? (
                      <div className="space-y-2">
                        <Input
                          label={t('workflows.graphLabel')}
                          value={String((selectedNode.data as any)?.label || '')}
                          onChange={(e) =>
                            updateNodeData(selectedNode.id, (data) => ({
                              ...data,
                              label: e.target.value,
                            }))
                          }
                        />

                        {selectedNodeType === 'skill' ? (
                          <>
                            <label className="block text-xs text-gray-600 dark:text-gray-300">
                              {t('workflows.graphSkillSelect')}
                            </label>
                            <select
                              className="block w-full rounded border border-gray-300 bg-white px-2 py-1.5 text-xs dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                              value={String(selectedNodeConfig.skill_id || '')}
                              onChange={(e) => updateNodeConfig('skill_id', e.target.value)}
                            >
                              <option value="">{t('workflows.graphSkillPlaceholder')}</option>
                              {skills.map((skill) => (
                                <option key={skill.id} value={skill.id}>
                                  {skill.name}
                                </option>
                              ))}
                            </select>
                            <div className="grid grid-cols-2 gap-2">
                              <Input
                                label={t('workflows.graphRetryCount')}
                                type="number"
                                value={String(selectedNodeConfig.retry_count ?? 0)}
                                onChange={(e) => updateNodeConfig('retry_count', toSafeInt(e.target.value, 0))}
                              />
                              <Input
                                label={t('workflows.graphTimeoutSec')}
                                type="number"
                                value={String(selectedNodeConfig.timeout_seconds ?? 0)}
                                onChange={(e) => updateNodeConfig('timeout_seconds', toSafeInt(e.target.value, 0))}
                              />
                            </div>
                            <div>
                              <div className="flex items-center justify-between">
                                <label className="block text-xs text-gray-600 dark:text-gray-300">
                                  {t('workflows.graphPayloadMapping')}
                                </label>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setAdvancedMapOpen((v) => !v)}
                                  title={advancedMapOpen ? t('workflows.graphCollapse') : t('workflows.graphExpand')}
                                >
                                  {advancedMapOpen ? '−' : '+'}
                                </Button>
                              </div>
                              {advancedMapOpen ? (
                                <textarea
                                  className="mt-1 h-28 w-full rounded border border-gray-300 bg-white px-2 py-1.5 font-mono text-xs dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                                  value={JSON.stringify(selectedNodeConfig.payload_template || {}, null, 2)}
                                  onChange={(e) => {
                                    try {
                                      updateNodeConfig('payload_template', JSON.parse(e.target.value || '{}'))
                                    } catch {
                                      // ignore temporary parse errors
                                    }
                                  }}
                                />
                              ) : (
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  {t('workflows.graphPayloadMappingHint')}
                                </p>
                              )}
                            </div>
                          </>
                        ) : null}

                        {selectedNodeType === 'condition' ? (
                          <div className="space-y-2">
                            <Input
                              label={t('workflows.graphConditionLeft')}
                              value={String(selectedNodeConfig.left || '')}
                              onChange={(e) => updateNodeConfig('left', e.target.value)}
                            />
                            <label className="block text-xs text-gray-600 dark:text-gray-300">
                              {t('workflows.graphConditionOp')}
                            </label>
                            <select
                              className="block w-full rounded border border-gray-300 bg-white px-2 py-1.5 text-xs dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                              value={String(selectedNodeConfig.op || '==')}
                              onChange={(e) => updateNodeConfig('op', e.target.value)}
                            >
                              <option value="==">==</option>
                              <option value="!=">!=</option>
                            </select>
                            <Input
                              label={t('workflows.graphConditionRight')}
                              value={String(selectedNodeConfig.right ?? '')}
                              onChange={(e) => updateNodeConfig('right', e.target.value)}
                            />
                          </div>
                        ) : null}

                        {selectedNodeType === 'approval' ? (
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {t('workflows.graphApprovalHint')}
                          </p>
                        ) : null}

                        {selectedNodeType === 'start' || selectedNodeType === 'end' ? (
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {t('workflows.graphNodeNoConfig')}
                          </p>
                        ) : null}
                      </div>
                    ) : null}

                    {selectedEdge ? (
                      <div className="space-y-2">
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {t('workflows.graphEdgeHint')}
                        </p>
                        <label className="block text-xs text-gray-600 dark:text-gray-300">
                          {t('workflows.graphEdgeCondition')}
                        </label>
                        <select
                          className="block w-full rounded border border-gray-300 bg-white px-2 py-1.5 text-xs dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                          value={typeof selectedEdge.label === 'string' ? selectedEdge.label : ''}
                          onChange={(e) => {
                            const val = e.target.value
                            setEdges((prev) =>
                              prev.map((edge) => (edge.id === selectedEdge.id ? { ...edge, label: val } : edge)),
                            )
                          }}
                        >
                          <option value="">{t('workflows.graphEdgeDefault')}</option>
                          <option value="true">true</option>
                          <option value="false">false</option>
                        </select>
                      </div>
                    ) : null}
                  </TabPanel>

                  <TabPanel id="json" activeTab={selectedTab}>
                    <div className="space-y-2">
                      <p className="text-xs text-gray-500 dark:text-gray-400">{t('workflows.graphJsonHint')}</p>
                      <textarea
                        className="h-72 w-full rounded border border-gray-300 bg-white px-2 py-1.5 font-mono text-xs dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                        value={jsonDraft}
                        onChange={(e) => setJsonDraft(e.target.value)}
                      />
                      {jsonError ? <p className="text-xs text-red-600 dark:text-red-400">{jsonError}</p> : null}
                      <div className="flex justify-end">
                        <Button size="sm" variant="secondary" onClick={applyJsonDraft}>
                          {t('workflows.graphApplyJson')}
                        </Button>
                      </div>
                    </div>
                  </TabPanel>
                </>
              )}
            </div>
          </aside>
        ) : null}
      </div>
    </div>
  )
}
