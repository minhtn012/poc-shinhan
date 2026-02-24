---
title: "Template Edit & Version Update Flow"
description: "Add template metadata editing and version update/bump flow to OCR Template POC"
status: done
priority: P2
effort: 3h
branch: main
tags: [vue3, element-plus, template-management, ocr]
created: 2026-02-24
---

# Template Edit & Version Update Flow

## Summary

Two missing features in the OCR Template POC:
1. **Template Edit** -- edit template metadata (name, description) from the list page
2. **Version Update Flow** -- create new version from existing version's fields, or navigate to edit a version's annotations

## Current State

- `template-list-view.vue` has only Delete action per row
- `template-detail-view.vue` shows version list with "Set Active" but no edit/clone/new-version actions
- `template-create-view.vue` is a 3-step wizard (upload + annotate + confirm) that creates a brand-new template+version
- `Template` type has `id`, `name`, `activeVersionId`, `createdAt` -- no `description` field yet
- `template.service.ts` has no `updateTemplate()` function
- No route for editing an existing version's annotations

## Phases

| # | Phase | Status | Effort |
|---|-------|--------|--------|
| 1 | [Template Edit](./phase-01-template-edit.md) | done | 1h |
| 2 | [Version Update Flow](./phase-02-version-update-flow.md) | done | 2h |

## Key Dependencies

- Element Plus `ElDialog`, `ElForm` components (already installed)
- Existing `annotation-canvas.vue` + `field-sidebar.vue` (reused)
- `use-image-store.ts` for loading version images by key
- No new npm packages needed

## Architecture

```
template-list-view.vue  -->  [Edit button]  -->  ElDialog inline (edit name/desc)
template-detail-view.vue --> [New Version from v1] --> template-create-view.vue?from=<versionId>
                          --> [View/Edit fields]    --> /templates/:id/versions/:vid (new route)
```

## Constraints

- No breaking changes to localStorage schema (add `description` field, nullable)
- Keep files under 200 lines
- Reuse existing annotation components
