export const ALL_PERMISSIONS = [
  'users:read', 'users:write',
  'conversations:read', 'conversations:write',
  'knowledge:read', 'knowledge:write',
  'skills:read', 'skills:write',
  'agents:read', 'agents:write',
  'settings:read', 'settings:write',
  'channels:read', 'channels:write',
  'dashboard:read',
  'speech:read', 'speech:write',
] as const

export const PERMISSION_LABELS: Record<string, string> = {
  'users:read': 'View users',
  'users:write': 'Manage users',
  'conversations:read': 'View conversations',
  'conversations:write': 'Manage conversations',
  'knowledge:read': 'View knowledge',
  'knowledge:write': 'Manage knowledge',
  'skills:read': 'View skills',
  'skills:write': 'Manage skills',
  'agents:read': 'View agents',
  'agents:write': 'Manage agents',
  'settings:read': 'View settings',
  'settings:write': 'Manage settings',
  'channels:read': 'View channels',
  'channels:write': 'Manage channels',
  'dashboard:read': 'View dashboard',
  'speech:read': 'Use speech',
  'speech:write': 'Manage speech',
}

export const FALLBACK_ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: [...ALL_PERMISSIONS],
  agent: [
    'conversations:read', 'conversations:write',
    'knowledge:read', 'skills:read', 'agents:read',
    'dashboard:read', 'speech:read', 'speech:write', 'channels:read',
  ],
}
