---
phase: 2
title: "Update Configs & Create Backend"
status: completed
priority: P1
effort: 15m
---

# Phase 2: Update Configs & Create Backend

## Context
- Parent plan: [plan.md](./plan.md)
- Depends on: [Phase 1](./phase-01-move-frontend-code.md)

## Overview
Update root-level configs for monorepo structure and create backend/ scaffold.

## Implementation Steps

### 1. Update `.gitignore`
Add monorepo patterns:
```
# Frontend
frontend/node_modules/
frontend/dist/

# Backend
backend/node_modules/
backend/dist/
backend/.env
```

### 2. Create `backend/` Directory
```
backend/
└── .gitkeep
```

### 3. Update Root `README.md`
Brief monorepo structure description with instructions for both frontend and backend.

### 4. Verify
- `cd frontend && npm run dev` → works
- `git status` → clean, all moves tracked

## Todo
- [ ] Update .gitignore for monorepo
- [ ] Create backend/ with .gitkeep
- [ ] Update README.md
- [ ] Final verification

## Success Criteria
- .gitignore covers both frontend/ and backend/
- backend/ directory exists
- README.md reflects new structure
- Frontend dev server runs successfully
