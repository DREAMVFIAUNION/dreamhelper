export const PERMISSIONS = {
  // Agent
  'agent:create': 'agent:create',
  'agent:read': 'agent:read',
  'agent:update': 'agent:update',
  'agent:delete': 'agent:delete',

  // Chat
  'chat:create': 'chat:create',
  'chat:read': 'chat:read',
  'chat:delete': 'chat:delete',

  // Knowledge Base
  'kb:create': 'kb:create',
  'kb:read': 'kb:read',
  'kb:update': 'kb:update',
  'kb:delete': 'kb:delete',
  'kb:upload': 'kb:upload',

  // Organization
  'org:manage': 'org:manage',
  'org:invite': 'org:invite',
  'org:billing': 'org:billing',

  // Admin
  'admin:all': 'admin:all',
} as const

export type Permission = keyof typeof PERMISSIONS
