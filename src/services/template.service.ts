/**
 * Template service — backed by real API (GET /get_templates, POST /update_template).
 * Uses an in-memory cache so sync getters work after loadFromApi() is called.
 * Local metadata (imageKey, field colors) is persisted in localStorage because
 * the API does not store those fields.
 */

import type { Template, TemplateVersion, TemplateField } from '@/types/template.types'
import type { ApiLayout, ApiLayoutField, ApiLayoutVersion, UpdateTemplateRequest } from '@/types/ocr.types'
import { getTemplates as apiGetTemplates, updateTemplate as apiUpdateTemplate } from './real-api'
import { yoloToNormalized, normalizedToYolo } from '@/lib/bbox-convert'

// ── Local metadata ─────────────────────────────────────────────────────────────
// The API doesn't persist imageKey or field colors, so we store them locally.

const META_KEY = 'ocr:tmpl:meta'
const FIELD_COLORS = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']

interface VersionMeta {
  imageKey: string
  colors: Record<string, string> // fieldName → hex color
}

function readMeta(): Record<string, VersionMeta> {
  try { return JSON.parse(localStorage.getItem(META_KEY) ?? '{}') } catch { return {} }
}

function writeMeta(meta: Record<string, VersionMeta>): void {
  localStorage.setItem(META_KEY, JSON.stringify(meta))
}

function defaultColor(idx: number): string {
  return FIELD_COLORS[idx % FIELD_COLORS.length]
}

// ── Version ID helpers ─────────────────────────────────────────────────────────
// Format: "{layout_id}::{version_str}"  e.g. "a46c19d2::v1"
// "::" cannot appear in hex layout IDs or typical version strings.

function makeVersionId(layoutId: string, version: string): string {
  return `${layoutId}::${version}`
}

function parseVersionId(versionId: string): { layoutId: string; versionStr: string } | null {
  const idx = versionId.indexOf('::')
  if (idx < 0) return null
  return { layoutId: versionId.slice(0, idx), versionStr: versionId.slice(idx + 2) }
}

// ── API ↔ internal conversion ──────────────────────────────────────────────────

function apiFieldToInternal(f: ApiLayoutField, idx: number, color: string): TemplateField {
  const [, cx, cy, w, h] = f.box
  return {
    id: `${f.field_name}_${idx}`,
    name: f.field_name,
    color,
    bbox: yoloToNormalized([cx, cy, w, h]),
  }
}

function apiVersionToInternal(layoutId: string, av: ApiLayoutVersion): TemplateVersion {
  const vid = makeVersionId(layoutId, av.version)
  const vMeta = readMeta()[vid]
  return {
    id: vid,
    templateId: layoutId,
    version: av.version,
    status: av.status,
    imageKey: vMeta?.imageKey ?? '',
    fields: av.fields.map((f, i) =>
      apiFieldToInternal(f, i, vMeta?.colors[f.field_name] ?? defaultColor(i))
    ),
    createdAt: '',
  }
}

function apiLayoutToTemplate(l: ApiLayout): Template {
  const activeVer = l.versions.find(v => v.status === 'active') ?? l.versions[0]
  return {
    id: l.layout_id,
    name: l.layout_name,
    activeVersionId: activeVer ? makeVersionId(l.layout_id, activeVer.version) : null,
    createdAt: '',
  }
}

function internalFieldToApi(f: TemplateField): ApiLayoutField {
  const [cx, cy, w, h] = normalizedToYolo(f.bbox)
  return { field_name: f.name, box: [0, cx, cy, w, h] }
}

// ── In-memory cache ────────────────────────────────────────────────────────────

let cache: ApiLayout[] = []

/** Fetch templates from API and populate the in-memory cache. Call this before sync getters. */
export async function loadFromApi(): Promise<void> {
  const res = await apiGetTemplates()
  cache = res.templates
}

// ── Sync getters (read from cache) ────────────────────────────────────────────

export function getTemplates(): Template[] {
  return cache.map(apiLayoutToTemplate)
}

export function getTemplate(id: string): Template | undefined {
  const layout = cache.find(l => l.layout_id === id)
  return layout ? apiLayoutToTemplate(layout) : undefined
}

export function getVersionsByTemplate(templateId: string): TemplateVersion[] {
  const layout = cache.find(l => l.layout_id === templateId)
  return layout?.versions.map(v => apiVersionToInternal(templateId, v)) ?? []
}

export function getVersion(versionId: string): TemplateVersion | undefined {
  const parsed = parseVersionId(versionId)
  if (!parsed) return undefined
  const layout = cache.find(l => l.layout_id === parsed.layoutId)
  const av = layout?.versions.find(v => v.version === parsed.versionStr)
  return av ? apiVersionToInternal(parsed.layoutId, av) : undefined
}

/** Suggest next version string based on existing versions in cache. */
export function suggestNextVersion(templateId: string): string {
  const layout = cache.find(l => l.layout_id === templateId)
  if (!layout?.versions.length) return 'v1'
  const nums = layout.versions
    .map(v => parseInt(v.version.replace(/\D/g, ''), 10))
    .filter(n => !isNaN(n))
  return `v${nums.length ? Math.max(...nums) + 1 : 1}`
}

// ── Async mutations ────────────────────────────────────────────────────────────

/**
 * Save a new version to an existing layout (action=update) or create a new layout (action=add).
 * @param layoutId - existing layout ID, or null to create new
 */
export async function saveVersion(
  layoutId: string | null,
  layoutName: string,
  version: string,
  imageKey: string,
  imageBase64: string,
  fields: TemplateField[]
): Promise<void> {
  const apiFields = fields.map(internalFieldToApi)
  const newApiVer: ApiLayoutVersion = { version, fields: apiFields, status: 'active' }

  let payload: UpdateTemplateRequest
  if (layoutId) {
    // Deactivate existing versions, then add new one
    const existing = cache.find(l => l.layout_id === layoutId)
    const prevVersions: ApiLayoutVersion[] = (existing?.versions ?? []).map(v => ({
      ...v, status: 'inactive',
    }))
    payload = {
      action: 'add',
      layout_id: layoutId,
      layout_name: layoutName,
      image_base64: imageBase64,
      versions: [...prevVersions, newApiVer],
    }
  } else {
    payload = { action: 'add', layout_id: null, layout_name: layoutName, image_base64: imageBase64, versions: [newApiVer] }
  }

  const res = await apiUpdateTemplate(payload)
  const finalLayoutId = res.layout_id ?? layoutId!
  const vid = makeVersionId(finalLayoutId, version)

  // Persist local meta (imageKey + colors)
  const meta = readMeta()
  meta[vid] = {
    imageKey,
    colors: Object.fromEntries(fields.map(f => [f.name, f.color])),
  }
  writeMeta(meta)
  await loadFromApi()
}

/** Update template name via API. Description is local-only and not sent to API. */
export async function updateTemplate(
  id: string,
  patch: { name?: string; description?: string }
): Promise<void> {
  if (!patch.name) return
  const layout = cache.find(l => l.layout_id === id)
  if (!layout) return
  await apiUpdateTemplate({
    action: 'add',
    layout_id: id,
    layout_name: patch.name,
    image_base64: '',
    versions: layout.versions,
  })
  await loadFromApi()
}

/** No delete API endpoint — no-op. */
export async function deleteTemplate(_id: string): Promise<void> {
  // The backend has no delete endpoint; data will remain on the server.
}

/** Set one version active, all others inactive for the same layout. */
export async function activateVersion(versionId: string): Promise<void> {
  const parsed = parseVersionId(versionId)
  if (!parsed) return
  const layout = cache.find(l => l.layout_id === parsed.layoutId)
  if (!layout) return
  const updatedVersions: ApiLayoutVersion[] = layout.versions.map(v => ({
    ...v, status: v.version === parsed.versionStr ? 'active' : 'inactive',
  }))
  await apiUpdateTemplate({
    action: 'add',
    layout_id: parsed.layoutId,
    layout_name: layout.layout_name,
    image_base64: '',
    versions: updatedVersions,
  })
  await loadFromApi()
}

/** Update fields for a specific version and persist to API. Colors saved locally. */
export async function updateVersionFields(versionId: string, fields: TemplateField[]): Promise<void> {
  const parsed = parseVersionId(versionId)
  if (!parsed) return
  const layout = cache.find(l => l.layout_id === parsed.layoutId)
  if (!layout) return

  // Update local color metadata
  const meta = readMeta()
  meta[versionId] = {
    imageKey: meta[versionId]?.imageKey ?? '',
    colors: Object.fromEntries(fields.map(f => [f.name, f.color])),
  }
  writeMeta(meta)

  const apiFields = fields.map(internalFieldToApi)
  const updatedVersions: ApiLayoutVersion[] = layout.versions.map(v =>
    v.version === parsed.versionStr ? { ...v, fields: apiFields } : v
  )
  await apiUpdateTemplate({
    action: 'add',
    layout_id: parsed.layoutId,
    layout_name: layout.layout_name,
    image_base64: '',
    versions: updatedVersions,
  })
  await loadFromApi()
}
