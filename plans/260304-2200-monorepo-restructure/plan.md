---
title: "Monorepo Restructure - Frontend/Backend Split"
description: "Move existing Vue 3 app into frontend/ folder and create backend/ folder"
status: completed
priority: P2
effort: 30m
branch: main
tags: [restructure, monorepo, devops]
created: 2026-03-04
---

# Monorepo Restructure Plan

## Overview
Restructure project from single Vue 3 app to monorepo with `frontend/` and `backend/` directories.

## Current Structure
```
poc-shinhan/
├── .claude/          # STAY at root
├── .git/             # STAY at root
├── .gitignore        # STAY at root
├── .env              # MOVE to frontend/
├── .vscode/          # STAY at root
├── plans/            # STAY at root
├── docs/             # STAY at root (if created)
├── README.md         # STAY at root
├── src/              # MOVE to frontend/
├── public/           # MOVE to frontend/
├── dist/             # MOVE to frontend/
├── node_modules/     # MOVE to frontend/
├── package.json      # MOVE to frontend/
├── package-lock.json # MOVE to frontend/
├── components.json   # MOVE to frontend/
├── index.html        # MOVE to frontend/
├── tsconfig*.json    # MOVE to frontend/
├── vite.config.ts    # MOVE to frontend/
```

## Target Structure
```
poc-shinhan/
├── .claude/
├── .git/
├── .gitignore        # Updated for monorepo
├── .vscode/
├── plans/
├── README.md         # Updated
├── frontend/         # Vue 3 app
│   ├── .env
│   ├── src/
│   ├── public/
│   ├── node_modules/
│   ├── package.json
│   ├── package-lock.json
│   ├── components.json
│   ├── index.html
│   ├── tsconfig*.json
│   └── vite.config.ts
└── backend/          # New - empty scaffold
    └── .gitkeep
```

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Move frontend code | completed | [phase-01](./phase-01-move-frontend-code.md) |
| 2 | Update configs & create backend | completed | [phase-02](./phase-02-update-configs-create-backend.md) |

## Key Risks
- `vite.config.ts` path alias `@` → `__dirname` sẽ tự resolve đúng vì relative
- `components.json` (shadcn-vue) paths relative → không cần sửa
- `node_modules` nên xóa và `npm install` lại trong `frontend/`
- `.gitignore` cần update pattern cho monorepo
