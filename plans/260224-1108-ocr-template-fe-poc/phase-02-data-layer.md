# Phase 2: Data Layer

## Context Links

- Plan overview: [plan.md](./plan.md)
- Depends on: [Phase 1](./phase-01-project-scaffold.md)

## Overview

- **Priority**: P1
- **Status**: completed
- **Effort**: 1h
- **Description**: Define TypeScript types, create localStorage/localforage services for CRUD, implement mock API functions for OCR processing.

## Key Insights

- Metadata (templates, versions, jobs) in localStorage — simple JSON stringify/parse
- Binary images in localforage (IndexedDB) — avoids 5MB localStorage limit
- Mock API simulates backend processing with configurable delays
- All IDs generated client-side via `crypto.randomUUID()`
- NormalizedBBox (0-1) is the storage format; pixel coords only used during rendering

## Requirements

### Functional
- TypeScript interfaces for all data models
- Template CRUD service (localStorage)
- TemplateVersion CRUD with status management
- Image storage composable (localforage)
- OCR job service
- Mock API: `mockPreprocess` (1.5s) and `mockOcr` (2s)

### Non-Functional
- Type-safe across entire data layer
- Services are pure functions, no Vue reactivity (composables wrap if needed)
- localforage operations handle errors gracefully

## Architecture

```
src/
├── types/
│   ├── template.types.ts    # Template, TemplateVersion, TemplateField, NormalizedBBox
│   └── ocr.types.ts         # OcrJob, OcrFieldResult
├── services/
│   ├── template.service.ts  # CRUD for templates + versions (localStorage)
│   ├── ocr.service.ts       # CRUD for OCR jobs (localStorage)
│   └── mock-api.ts          # mockPreprocess, mockOcr
├── composables/
│   └── use-image-store.ts   # localforage wrapper for image blobs
```

### Storage Keys
```
localStorage:
  "ocr:templates"  → Template[]
  "ocr:versions"   → TemplateVersion[]
  "ocr:jobs"       → OcrJob[]

localforage:
  "img:{id}"       → Blob (image file)
```

## Related Code Files

### Create
- `src/types/template.types.ts`
- `src/types/ocr.types.ts`
- `src/services/template.service.ts`
- `src/services/ocr.service.ts`
- `src/services/mock-api.ts`
- `src/composables/use-image-store.ts`

## Implementation Steps

### 1. Create `src/types/template.types.ts`
```typescript
export interface NormalizedBBox {
  x: number  // 0-1, left edge relative to image width
  y: number  // 0-1, top edge relative to image height
  w: number  // 0-1, width relative to image width
  h: number  // 0-1, height relative to image height
}

export interface TemplateField {
  id: string
  name: string
  color: string    // hex color for bbox display
  bbox: NormalizedBBox
}

export interface Template {
  id: string
  name: string
  activeVersionId: string | null
  createdAt: string  // ISO
}

export interface TemplateVersion {
  id: string
  templateId: string
  version: string      // e.g. "v1", "v2"
  status: 'active' | 'inactive'
  imageKey: string     // localforage key: "img:{id}"
  fields: TemplateField[]
  createdAt: string
}
```

### 2. Create `src/types/ocr.types.ts`
```typescript
import type { NormalizedBBox } from './template.types'

export interface OcrFieldResult {
  fieldId: string
  fieldName: string
  bbox: NormalizedBBox
  value: string
  confidence: number   // 0-1
  edited: boolean
}

export type OcrJobStatus = 'pending' | 'processing' | 'done' | 'error'

export interface OcrJob {
  id: string
  templateVersionId: string
  templateName: string
  imageKey: string
  status: OcrJobStatus
  results: OcrFieldResult[]
  createdAt: string
}
```

### 3. Create `src/services/template.service.ts`
localStorage CRUD with these functions:
```typescript
const TEMPLATES_KEY = 'ocr:templates'
const VERSIONS_KEY = 'ocr:versions'

// Template CRUD
getTemplates(): Template[]
getTemplate(id: string): Template | undefined
createTemplate(name: string): Template
deleteTemplate(id: string): void

// Version CRUD
getVersionsByTemplate(templateId: string): TemplateVersion[]
getVersion(id: string): TemplateVersion | undefined
getActiveVersion(templateId: string): TemplateVersion | undefined
createVersion(templateId: string, version: string, imageKey: string, fields: TemplateField[]): TemplateVersion
  // Also: set new version active, deactivate previous active
activateVersion(versionId: string): void
  // Deactivate all other versions for same template, activate this one
  // Update template.activeVersionId
```

Helper: `readList<T>(key)`, `writeList<T>(key, data)` for localStorage JSON.

### 4. Create `src/services/ocr.service.ts`
```typescript
const JOBS_KEY = 'ocr:jobs'

getJobs(): OcrJob[]
getJob(id: string): OcrJob | undefined
createJob(params: { templateVersionId, templateName, imageKey }): OcrJob
updateJobStatus(id: string, status: OcrJobStatus): void
updateJobResults(id: string, results: OcrFieldResult[]): void
updateFieldValue(jobId: string, fieldId: string, value: string): void
  // Mark edited: true
deleteJob(id: string): void
```

### 5. Create `src/services/mock-api.ts`
```typescript
import type { TemplateVersion } from '@/types/template.types'
import type { OcrFieldResult } from '@/types/ocr.types'
import { getTemplates, getActiveVersion } from './template.service'

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// Simulate template detection from uploaded image
export async function mockPreprocess(_blob: Blob): Promise<{
  templateId: string
  confidence: number
} | null> {
  await delay(1500)
  const templates = getTemplates()
  if (templates.length === 0) return null
  // Pick first template with active version
  const match = templates.find(t => t.activeVersionId)
  if (!match) return null
  return { templateId: match.id, confidence: 0.92 }
}

// Simulate OCR extraction using template fields
export async function mockOcr(
  _blob: Blob,
  version: TemplateVersion
): Promise<OcrFieldResult[]> {
  await delay(2000)
  // Generate mock values for each field
  const sampleValues: Record<string, string> = {
    'name': 'Nguyen Van A',
    'date': '2026-01-15',
    'amount': '15,000,000',
    'account': '1234-5678-9012',
    'id_number': '079012345678',
    'address': '123 Le Loi, Q1, HCM'
  }
  return version.fields.map(field => ({
    fieldId: field.id,
    fieldName: field.name,
    bbox: { ...field.bbox },
    value: sampleValues[field.name.toLowerCase()] ?? `Sample ${field.name}`,
    confidence: 0.75 + Math.random() * 0.2,
    edited: false
  }))
}
```

### 6. Create `src/composables/use-image-store.ts`
```typescript
import localforage from 'localforage'

const store = localforage.createInstance({ name: 'ocr-images' })

export function useImageStore() {
  async function saveImage(key: string, blob: Blob): Promise<void> {
    await store.setItem(key, blob)
  }

  async function getImage(key: string): Promise<Blob | null> {
    return await store.getItem<Blob>(key)
  }

  async function getImageUrl(key: string): Promise<string | null> {
    const blob = await getImage(key)
    if (!blob) return null
    return URL.createObjectURL(blob)
  }

  async function removeImage(key: string): Promise<void> {
    await store.removeItem(key)
  }

  return { saveImage, getImage, getImageUrl, removeImage }
}
```

### 7. Verify
- Import types in a test file, ensure no TS errors
- Call service functions from browser console to verify localStorage read/write
- Test mock API delays return expected data shapes

## Todo List

- [ ] Create template.types.ts
- [ ] Create ocr.types.ts
- [ ] Create template.service.ts with all CRUD functions
- [ ] Create ocr.service.ts with all CRUD functions
- [ ] Create mock-api.ts with mockPreprocess + mockOcr
- [ ] Create use-image-store.ts composable
- [ ] Verify TS compilation passes
- [ ] Manual test: create template + version via service, verify localStorage

## Success Criteria

- All types compile with strict mode
- template.service: create template → create version → activate → getActiveVersion returns correct version
- ocr.service: create job → update results → updateFieldValue sets edited=true
- mock-api: mockPreprocess resolves after ~1.5s, mockOcr after ~2s with correct shape
- use-image-store: save blob → getImageUrl returns valid object URL

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| localStorage size limit (~5MB) for metadata | Low | Metadata is small JSON, images use localforage |
| localforage async + Vue reactivity | Med | Wrap in composable, use async/await consistently |
| Mock API too simplistic for demo | Low | Acceptable for POC, document limitations |

## Security Considerations

- No sensitive data in localStorage for POC
- Object URLs from createObjectURL should be revoked when no longer needed (onUnmounted)

## Next Steps

- Phase 3: Annotation canvas (consumes types + image store)
