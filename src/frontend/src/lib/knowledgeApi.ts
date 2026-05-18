/** Map backend knowledge API (snake_case) to UI types */

export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  documentCount: number
  createdAt: string
  updatedAt: string
}

export interface KnowledgeDocument {
  id: string
  knowledgeBaseId: string
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'indexed'
  fileSize: number
  createdAt: string
}

export function mapKnowledgeBase(raw: Record<string, unknown>): KnowledgeBase {
  return {
    id: String(raw.id),
    name: String(raw.name),
    description: raw.description != null ? String(raw.description) : undefined,
    documentCount: Number(raw.document_count ?? raw.documentCount ?? 0),
    createdAt: String(raw.created_at ?? raw.createdAt ?? ''),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? ''),
  }
}

export function mapDocument(raw: Record<string, unknown>): KnowledgeDocument {
  const status = String(raw.status ?? 'pending')
  return {
    id: String(raw.id),
    knowledgeBaseId: String(raw.knowledge_base_id ?? raw.knowledgeBaseId ?? ''),
    filename: String(raw.title ?? raw.filename ?? '未命名'),
    status: status === 'indexed' ? 'completed' : (status as KnowledgeDocument['status']),
    fileSize: Number(raw.file_size ?? raw.fileSize ?? 0),
    createdAt: String(raw.created_at ?? raw.createdAt ?? ''),
  }
}

export function uiStatusLabel(status: string): string {
  switch (status) {
    case 'completed':
    case 'indexed':
      return '已完成'
    case 'processing':
      return '处理中'
    case 'failed':
      return '失败'
    default:
      return '待处理'
  }
}
