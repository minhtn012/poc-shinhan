# Phase 6: Polish & UX

## Context Links

- Plan overview: [plan.md](./plan.md)
- Depends on: [Phase 4](./phase-04-template-views.md) + [Phase 5](./phase-05-ocr-views.md)

## Overview

- **Priority**: P2
- **Status**: completed
- **Effort**: 1h
- **Description**: Add loading states, error handling, empty states, responsive adjustments, and general UX polish across all views.

## Key Insights

- POC first impression matters — loading skeleton, empty states, transitions
- Error boundaries prevent blank screens on unexpected errors
- Consistent spacing + typography via Element Plus variables
- Keyboard shortcuts for power users: Escape to deselect, Delete to remove field

## Requirements

### Functional
- Loading skeletons for async data (image loading, service calls)
- Empty states with helpful CTAs for all list views
- Error boundary component catches render errors
- Toast notifications for all actions (save, delete, export)
- Breadcrumb navigation on detail views
- Confirmation dialog before destructive actions (delete template, delete job)
- Keyboard: Escape deselects in annotation canvas, Delete removes selected field

### Non-Functional
- Consistent padding/margin (use CSS variables)
- Smooth transitions between wizard steps
- Responsive: sidebar collapses on narrow screens
- Clean global styles (scrollbar, focus rings)

## Architecture

```
src/
├── components/common/
│   ├── app-layout.vue        # UPDATE: add breadcrumbs slot
│   └── version-badge.vue     # Already exists
├── style.css                 # UPDATE: global polish styles
```

No new files — mostly updates to existing components.

## Related Code Files

### Modify
- `src/style.css` — global styles, transitions, scrollbar
- `src/components/common/app-layout.vue` — breadcrumbs, responsive sidebar
- `src/views/template-list-view.vue` — empty state, loading skeleton
- `src/views/template-create-view.vue` — step transitions, validation messages
- `src/views/template-detail-view.vue` — breadcrumbs, empty state
- `src/views/ocr-list-view.vue` — empty state, loading, confirm delete
- `src/views/ocr-upload-view.vue` — better error messages, template check
- `src/views/ocr-review-view.vue` — loading state, breadcrumbs
- `src/components/annotation/annotation-canvas.vue` — keyboard shortcuts
- `src/components/ocr/results-table.vue` — row highlight style for hover

## Implementation Steps

### 1. Global styles (`src/style.css`)

Add:
```css
/* Smooth transitions */
.el-main { transition: padding 0.3s; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Custom scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 3px; }

/* Consistent page header */
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { margin: 0; }
```

### 2. Loading states

Add `el-skeleton` to list views while data loads:
```vue
<el-skeleton v-if="loading" :rows="5" animated />
<el-table v-else ... />
```

For image loading in canvas and overlay:
```vue
<div v-if="imageLoading" class="loading-overlay">
  <el-icon class="is-loading" size="32"><Loading /></el-icon>
</div>
```

### 3. Empty states

Template list:
```vue
<el-empty v-if="!templates.length" description="No templates yet">
  <el-button type="primary" @click="router.push('/templates/create')">
    Create Your First Template
  </el-button>
</el-empty>
```

OCR list:
```vue
<el-empty v-if="!jobs.length" description="No OCR jobs yet">
  <el-button type="primary" @click="router.push('/ocr/new')">
    Start First OCR Job
  </el-button>
</el-empty>
```

### 4. Confirmation dialogs

Before delete actions:
```typescript
async function deleteJob(id: string) {
  await ElMessageBox.confirm(
    'This will permanently delete the OCR job. Continue?',
    'Delete Job',
    { type: 'warning' }
  )
  ocrService.deleteJob(id)
  loadJobs()  // refresh list
  ElMessage.success('Job deleted')
}
```

Same pattern for template delete.

### 5. Toast notifications

Every action gets feedback:
- Save template → `ElMessage.success('Template saved')`
- Delete → `ElMessage.success('Deleted')`
- Export → `ElMessage.success('JSON exported')`
- Error → `ElMessage.error(message)`

### 6. Keyboard shortcuts in annotation canvas

```typescript
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    clearSelection()
  }
  if (event.key === 'Delete' || event.key === 'Backspace') {
    if (selectedFieldId.value) {
      deleteField(selectedFieldId.value)
    }
  }
}
onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
```

### 7. Responsive sidebar

In app-layout.vue:
```typescript
const isNarrow = ref(window.innerWidth < 768)
onMounted(() => {
  window.addEventListener('resize', () => {
    isNarrow.value = window.innerWidth < 768
  })
})
```

Collapse sidebar when `isNarrow` is true.

### 8. OCR upload: check templates exist

At top of ocr-upload-view:
```vue
<el-alert v-if="!hasTemplates" type="warning" show-icon :closable="false"
  title="No templates found"
  description="Create a template first before running OCR."
>
  <el-button size="small" @click="router.push('/templates/create')">
    Create Template
  </el-button>
</el-alert>
```

### 9. Breadcrumbs

In detail/review views:
```vue
<el-breadcrumb>
  <el-breadcrumb-item :to="{ path: '/templates' }">Templates</el-breadcrumb-item>
  <el-breadcrumb-item>{{ template?.name }}</el-breadcrumb-item>
</el-breadcrumb>
```

### 10. Final review pass

- Check all views render correctly
- Verify no console errors
- Test full workflow: login → create template → create OCR job → review → export

## Todo List

- [ ] Add global CSS styles (transitions, scrollbar, page-header)
- [ ] Add loading skeletons to list views
- [ ] Add empty states with CTAs to all list views
- [ ] Add confirmation dialogs before destructive actions
- [ ] Add toast notifications for all actions
- [ ] Add keyboard shortcuts (Escape, Delete) in annotation canvas
- [ ] Add responsive sidebar collapse
- [ ] Add template existence check on OCR upload page
- [ ] Add breadcrumbs to detail views
- [ ] Full workflow smoke test

## Success Criteria

- All loading states show skeleton/spinner
- Empty states show helpful message + CTA button
- Delete requires confirmation dialog
- All actions show toast feedback
- Escape deselects in canvas, Delete removes field
- Sidebar collapses on narrow viewport
- OCR upload warns if no templates
- No console errors during full workflow
- Clean, professional appearance

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Polish scope creep | Low | Timebox to 1h, focus on high-impact items |
| CSS conflicts with Element Plus | Low | Use scoped styles + CSS variables |

## Security Considerations

- No new security concerns in polish phase
- Confirmation dialogs prevent accidental data loss

## Next Steps

- POC complete, ready for demo
- Future: real backend API, user management, actual OCR engine integration
