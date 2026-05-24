import api from './api'

export interface ChannelTemplate {
  id: string
  name: string
  description: string | null
  category: string
  icon: string | null
  price_monthly_cents: number
  price_yearly_cents: number
  trial_days: number
  default_theme: Record<string, any> | null
  default_welcome_message: string | null
  default_offline_message: string | null
  created_at: string
}

export interface MyChannel {
  id: string
  name: string
  short_code: string | null
  channel_category: string
  template_id: string | null
  plan: string
  trial_ends_at: string | null
  enabled: boolean
  welcome_message: string | null
  offline_message: string | null
  theme: Record<string, any> | null
  usage_messages_month: number
  usage_tokens_month: number
  usage_messages_limit: number
  usage_tokens_limit: number
  created_at: string
  updated_at: string
}

export interface EmbedCode {
  agent_id: string
  embed_script: string
  widget_url: string
}

export interface PortalDashboardStats {
  total_channels: number
  active_channels: number
  total_conversations: number
  messages_today: number
  total_messages_month: number
  total_tokens_month: number
  plan: string | null
  trial_ends_at: string | null
}

export interface ChannelKnowledgeBase {
  id: string
  name: string
  description?: string | null
  document_count: number
  source: 'owned' | 'system'
  can_upload?: boolean
  can_delete?: boolean
}

export const portalApi = {
  getTemplates: () => api.get<ChannelTemplate[]>('/templates'),
  getTemplate: (id: string) => api.get<ChannelTemplate>(`/templates/${id}`),

  rentChannel: (templateId: string, name?: string) =>
    api.post<MyChannel>('/portal/channels/rent', { template_id: templateId, name }),

  getMyChannels: () => api.get<MyChannel[]>('/portal/channels'),
  getMyChannel: (id: string) => api.get<MyChannel>(`/portal/channels/${id}`),
  updateMyChannel: (id: string, data: Partial<MyChannel>) =>
    api.put<MyChannel>(`/portal/channels/${id}`, data),
  deleteMyChannel: (id: string) => api.delete(`/portal/channels/${id}`),

  getEmbedCode: (id: string) => api.get<EmbedCode>(`/portal/channels/${id}/embed`),

  /** Resume persistent portal chat for a channel (same thread across visits). */
  resumeChannelConversation: (channelId: string) =>
    api.post<{ id: string; messages?: unknown[] }>(
      `/portal/channels/${channelId}/conversation/resume`,
    ),
  getDashboardStats: () => api.get<PortalDashboardStats>('/portal/dashboard'),

  listChannelKnowledgeBases: (channelId: string) =>
    api.get<ChannelKnowledgeBase[]>(`/portal/channels/${channelId}/knowledge-bases`),

  createChannelKnowledgeBase: (channelId: string, data: { name: string; description?: string }) =>
    api.post<{ id: string; name: string }>(
      `/portal/channels/${channelId}/knowledge-bases`,
      data,
    ),

  removeChannelKnowledgeBase: (channelId: string, kbId: string) =>
    api.delete<{ ok: boolean; deleted: boolean }>(
      `/portal/channels/${channelId}/knowledge-bases/${kbId}`,
    ),

  uploadChannelDocument: (channelId: string, kbId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.upload(`/portal/channels/${channelId}/knowledge-bases/${kbId}/import-file`, form)
  },
}
