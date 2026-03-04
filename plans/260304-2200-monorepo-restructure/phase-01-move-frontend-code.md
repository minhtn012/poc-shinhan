---
phase: 1
title: "Move Frontend Code"
status: completed
priority: P1
effort: 15m
---

# Phase 1: Move Frontend Code

## Context
- Parent plan: [plan.md](./plan.md)

## Overview
Move all Vue 3 app files into `frontend/` subdirectory using `git mv` to preserve history.

## Files to Move
```
.env → frontend/.env
src/ → frontend/src/
public/ → frontend/public/
dist/ → frontend/dist/
index.html → frontend/index.html
package.json → frontend/package.json
package-lock.json → frontend/package-lock.json
components.json → frontend/components.json
tsconfig.json → frontend/tsconfig.json
tsconfig.app.json → frontend/tsconfig.app.json
tsconfig.node.json → frontend/tsconfig.node.json
vite.config.ts → frontend/vite.config.ts
```

## Files to KEEP at Root
- `.git/`, `.claude/`, `.gitignore`, `.vscode/`, `plans/`, `docs/`, `README.md`

## Implementation Steps
1. Create `frontend/` directory
2. `git mv` each file/folder to `frontend/`
3. Delete `node_modules/` (not tracked, will reinstall)
4. Delete `dist/` (build artifact)
5. Run `cd frontend && npm install` to recreate node_modules
6. Run `cd frontend && npm run build` to verify build works

## Todo
- [ ] Create frontend directory
- [ ] git mv all frontend files
- [ ] Remove node_modules and dist
- [ ] npm install in frontend/
- [ ] Verify build works

## Success Criteria
- All frontend files moved to `frontend/`
- `npm run dev` works from `frontend/`
- Git history preserved via `git mv`
