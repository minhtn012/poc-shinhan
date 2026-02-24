# Phase 1: Template Edit

## Context Links

- Plan overview: [plan.md](./plan.md)
- Current list view: `src/views/template-list-view.vue` (126 lines)
- Service layer: `src/services/template.service.ts` (123 lines)
- Types: `src/types/template.types.ts` (31 lines)

## Overview

- **Priority:** P2
- **Status:** done
- **Effort:** 1h
- **Description:** Add inline edit dialog for template metadata (name, description) accessible from both the template list and detail views

## Key Insights

- `Template` interface currently has no `description` field -- add it as optional `string | undefined`
- `template.service.ts` has no `updateTemplate()` -- needs a simple patch function
- The list view already uses `@row-click` for navigation; edit button must use `@click.stop` to prevent row click
- Element Plus `ElDialog` + `ElForm` with validation is the established pattern in this codebase

## Requirements

### Functional
- FR-1: Edit button visible on each template row in template-list-view
- FR-2: Clicking Edit opens a dialog with name + description fields, pre-filled
- FR-3: Save updates localStorage via new `updateTemplate()` service method
- FR-4: Template detail view header also shows edit button
- FR-5: Description shown in detail view header area

### Non-Functional
- No breaking changes to existing `ocr:templates` localStorage key format
- `description` field is optional/nullable for backward compat with existing data

## Architecture

```
User clicks Edit -> ElDialog opens (inline in same view)
  -> name (required) + description (optional) inputs
  -> Save calls updateTemplate(id, { name, description })
  -> Dialog closes, list refreshes
```

No new routes or views needed. Dialog is local component state within template-list-view and template-detail-view.

## Related Code Files

### Files to Modify
| File | Change |
|------|--------|
| `src/types/template.types.ts` | Add `description?: string` to `Template` interface |
| `src/services/template.service.ts` | Add `updateTemplate(id, patch)` function |
| `src/views/template-list-view.vue` | Add Edit button + ElDialog for editing |
| `src/views/template-detail-view.vue` | Add Edit button in header + show description |

### Files to Create
None.

### Files to Delete
None.

## Implementation Steps

### Step 1: Update Template type (template.types.ts)

Add `description?: string` to the `Template` interface after `name`:

```ts
export interface Template {
  id: string
  name: string
  description?: string      // <-- NEW
  activeVersionId: string | null
  createdAt: string
}
```

### Step 2: Add updateTemplate service method (template.service.ts)

Add after `deleteTemplate`:

```ts
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
```

### Step 3: Add edit dialog to template-list-view.vue

Add an Edit button in the Actions column next to Delete:

```html
<el-button size="small" plain @click.stop="openEditDialog(row)">
  Edit
</el-button>
```

Add ElDialog at bottom of template, bound to `editDialogVisible` ref:

```html
<el-dialog v-model="editDialogVisible" title="Edit Template" width="460px">
  <el-form label-position="top">
    <el-form-item label="Name" required>
      <el-input v-model="editForm.name" />
    </el-form-item>
    <el-form-item label="Description">
      <el-input v-model="editForm.description" type="textarea" :rows="3" />
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="editDialogVisible = false">Cancel</el-button>
    <el-button type="primary" :disabled="!editForm.name.trim()" @click="saveEdit">
      Save
    </el-button>
  </template>
</el-dialog>
```

Script additions:

```ts
const editDialogVisible = ref(false)
const editForm = ref({ id: '', name: '', description: '' })

function openEditDialog(row: TableRow): void {
  const tmpl = templateService.getTemplate(row.id)
  if (!tmpl) return
  editForm.value = { id: tmpl.id, name: tmpl.name, description: tmpl.description ?? '' }
  editDialogVisible.value = true
}

function saveEdit(): void {
  templateService.updateTemplate(editForm.value.id, {
    name: editForm.value.name.trim(),
    description: editForm.value.description.trim() || undefined
  })
  editDialogVisible.value = false
  ElMessage.success('Template updated')
  loadTemplates()
}
```

### Step 4: Add edit capability to template-detail-view.vue

Add Edit button next to the template name in header:

```html
<div class="page-header">
  <h2>{{ template?.name }}</h2>
  <div style="display: flex; gap: 8px">
    <el-button size="small" @click="openEditDialog" v-if="template">Edit</el-button>
    <el-button @click="router.push('/templates')">Back</el-button>
  </div>
</div>
```

Show description below header if present:

```html
<el-text v-if="template?.description" type="info" style="margin-bottom: 16px; display: block">
  {{ template.description }}
</el-text>
```

Add same edit dialog pattern (dialog + refs + openEditDialog + saveEdit functions). On save, also call `load()` to refresh.

## Todo List

- [x] Add `description?: string` to `Template` interface
- [x] Add `updateTemplate()` to `template.service.ts`
- [x] Add Edit button + dialog to `template-list-view.vue`
- [x] Add Edit button + description display + dialog to `template-detail-view.vue`
- [x] Manual test: create template, edit name/description, verify persistence
- [x] Run `npx vue-tsc --noEmit` to verify no type errors

## Success Criteria

- Edit button visible on each template row and in detail header
- Dialog pre-fills current name + description
- Saving persists to localStorage and reflects in UI immediately
- Existing templates without description field continue to work (backward compat)
- `vue-tsc --noEmit` passes

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| localStorage schema migration | Low | Low | `description` is optional, old data loads fine |
| File size exceeding 200 lines | Medium | Low | Dialog is minimal; both views stay well under 200 |

## Security Considerations

- Input sanitized via `.trim()`; no HTML rendering of description (plain text only)
- No new routes or permissions needed

## Next Steps

- Phase 2 depends on this completing first (version update flow uses updated template types)
