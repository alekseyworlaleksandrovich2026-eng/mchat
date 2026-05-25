/** Helpers for skill scope (server_ops vs tenant). */

export function skillScope(skill: {
  config?: Record<string, unknown> | null
}): string {
  const raw = skill.config?.scope
  if (raw == null) return 'tenant'
  return String(raw).trim().toLowerCase() || 'tenant'
}

export function isServerOpsSkill(skill: {
  config?: Record<string, unknown> | null
}): boolean {
  return skillScope(skill) === 'server_ops'
}

export function tenantSelectableSkills<T extends { config?: Record<string, unknown> | null }>(
  skills: T[],
): T[] {
  return skills.filter((s) => !isServerOpsSkill(s))
}
