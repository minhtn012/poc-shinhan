import type { Template, TemplateVersion, TemplateField } from '@/types/template.types'

const TEMPLATES_KEY = 'ocr:templates'
const VERSIONS_KEY = 'ocr:versions'

function readList<T>(key: string): T[] {
  try {
    return JSON.parse(localStorage.getItem(key) ?? '[]') as T[]
  } catch {
    return []
  }
}

function writeList<T>(key: string, data: T[]): void {
  localStorage.setItem(key, JSON.stringify(data))
}

// ---- Template CRUD ----

export function getTemplates(): Template[] {
  return readList<Template>(TEMPLATES_KEY)
}

export function getTemplate(id: string): Template | undefined {
  return getTemplates().find(t => t.id === id)
}

export function createTemplate(name: string): Template {
  const template: Template = {
    id: crypto.randomUUID(),
    name,
    activeVersionId: null,
    createdAt: new Date().toISOString()
  }
  const list = getTemplates()
  list.push(template)
  writeList(TEMPLATES_KEY, list)
  return template
}

export function updateTemplate(
  id: string,
  patch: { name?: string; description?: string }
): Template | undefined {
  const templates = getTemplates()
  const tmpl = templates.find(t => t.id === id)
  if (!tmpl) return undefined
  if (patch.name !== undefined) tmpl.name = patch.name
  if (patch.description !== undefined) tmpl.description = patch.description
  writeList(TEMPLATES_KEY, templates)
  return tmpl
}

export function deleteTemplate(id: string): void {
  const templates = getTemplates().filter(t => t.id !== id)
  writeList(TEMPLATES_KEY, templates)
  const versions = readList<TemplateVersion>(VERSIONS_KEY).filter(v => v.templateId !== id)
  writeList(VERSIONS_KEY, versions)
}

// ---- Version CRUD ----

export function getVersionsByTemplate(templateId: string): TemplateVersion[] {
  return readList<TemplateVersion>(VERSIONS_KEY).filter(v => v.templateId === templateId)
}

export function getVersion(id: string): TemplateVersion | undefined {
  return readList<TemplateVersion>(VERSIONS_KEY).find(v => v.id === id)
}

export function getActiveVersion(templateId: string): TemplateVersion | undefined {
  return readList<TemplateVersion>(VERSIONS_KEY).find(
    v => v.templateId === templateId && v.status === 'active'
  )
}

export function createVersion(
  templateId: string,
  version: string,
  imageKey: string,
  fields: TemplateField[]
): TemplateVersion {
  // Deactivate all existing versions for this template
  const allVersions = readList<TemplateVersion>(VERSIONS_KEY)
  for (const v of allVersions) {
    if (v.templateId === templateId) {
      v.status = 'inactive'
    }
  }

  const newVersion: TemplateVersion = {
    id: crypto.randomUUID(),
    templateId,
    version,
    status: 'active',
    imageKey,
    fields,
    createdAt: new Date().toISOString()
  }
  allVersions.push(newVersion)
  writeList(VERSIONS_KEY, allVersions)

  // Update template's activeVersionId
  const templates = getTemplates()
  const tmpl = templates.find(t => t.id === templateId)
  if (tmpl) {
    tmpl.activeVersionId = newVersion.id
    writeList(TEMPLATES_KEY, templates)
  }

  return newVersion
}

export function suggestNextVersion(templateId: string): string {
  const versions = getVersionsByTemplate(templateId)
  if (!versions.length) return 'v1'
  const nums = versions
    .map(v => parseInt(v.version.replace(/\D/g, ''), 10))
    .filter(n => !isNaN(n))
  const max = nums.length ? Math.max(...nums) : 0
  return `v${max + 1}`
}

export function activateVersion(versionId: string): void {
  const allVersions = readList<TemplateVersion>(VERSIONS_KEY)
  const target = allVersions.find(v => v.id === versionId)
  if (!target) return

  // Deactivate siblings
  for (const v of allVersions) {
    if (v.templateId === target.templateId) {
      v.status = 'inactive'
    }
  }
  target.status = 'active'
  writeList(VERSIONS_KEY, allVersions)

  // Update template activeVersionId
  const templates = getTemplates()
  const tmpl = templates.find(t => t.id === target.templateId)
  if (tmpl) {
    tmpl.activeVersionId = versionId
    writeList(TEMPLATES_KEY, templates)
  }
}
