# Phase 1: Project Scaffold

## Context Links

- Plan overview: [plan.md](./plan.md)
- Brainstorm: `../../reports/brainstorm-260224-1108-ocr-template-fe-poc.md`

## Overview

- **Priority**: P1 (foundation for everything)
- **Status**: completed
- **Effort**: 1h
- **Description**: Initialize Vite + Vue 3 + TS project, install all deps, configure router with auth guard, create app layout shell, and login page.

## Key Insights

- Login is hardcoded from `.env` — no real auth backend needed
- Auth guard uses Pinia store to check `isAuthenticated` flag
- Element Plus provides sidebar nav (el-menu) and layout primitives
- Keep router config simple: flat routes, one `beforeEach` guard

## Requirements

### Functional
- Vite project with Vue 3 + TypeScript
- All dependencies installed and configured
- Router with all 7 routes defined
- Auth guard redirects unauthenticated users to `/login`
- Login page validates against `VITE_AUTH_USER` / `VITE_AUTH_PASS`
- App layout with sidebar navigation and router-view

### Non-Functional
- Dev server starts without errors
- TypeScript strict mode enabled
- Path aliases configured (`@/` → `src/`)

## Architecture

```
src/
├── router/index.ts          # All routes + beforeEach guard
├── stores/auth.store.ts     # isAuthenticated, login(), logout()
├── stores/app.store.ts      # Global UI state (sidebar collapse, etc)
├── components/common/
│   └── app-layout.vue       # el-container + el-aside(menu) + router-view
├── views/login-view.vue     # Login form
├── App.vue                  # <router-view> only
├── main.ts                  # createApp, pinia, router, element-plus
├── env.d.ts                 # VITE_ env type declarations
└── style.css                # Global resets + Element Plus overrides
```

## Related Code Files

### Create
- `src/router/index.ts`
- `src/stores/auth.store.ts`
- `src/stores/app.store.ts`
- `src/components/common/app-layout.vue`
- `src/views/login-view.vue`
- `src/App.vue`
- `src/main.ts`
- `src/env.d.ts`
- `src/style.css`
- `.env` (with VITE_AUTH_USER, VITE_AUTH_PASS)
- `vite.config.ts`
- `tsconfig.json`, `tsconfig.app.json`

## Implementation Steps

### 1. Initialize Vite project
```bash
cd /data/data/poc-shinhan
npm create vite@latest . -- --template vue-ts
```
If project already exists, init manually. Ensure `package.json` has `"type": "module"`.

### 2. Install dependencies
```bash
npm install vue-router@4 pinia element-plus @element-plus/icons-vue d3 localforage @tanstack/vue-query
npm install -D @types/d3 sass-embedded
```

### 3. Configure Vite
In `vite.config.ts`:
- Set `resolve.alias`: `@` → `src/`
- Set `server.port`: 3000

### 4. Create `.env`
```env
VITE_AUTH_USER=admin
VITE_AUTH_PASS=shinhan2024
```

### 5. Create `src/env.d.ts`
Declare `ImportMetaEnv` with `VITE_AUTH_USER` and `VITE_AUTH_PASS`.

### 6. Create auth store (`src/stores/auth.store.ts`)
```typescript
// defineStore('auth')
// state: isAuthenticated (check sessionStorage on init)
// actions: login(user, pass) → validate against import.meta.env, logout()
// persist auth flag in sessionStorage so refresh keeps session
```

### 7. Create app store (`src/stores/app.store.ts`)
```typescript
// defineStore('app')
// state: sidebarCollapsed: boolean
// actions: toggleSidebar()
```

### 8. Create router (`src/router/index.ts`)
Routes:
- `/login` → LoginView (no layout)
- `/templates` → TemplateListView (inside AppLayout)
- `/templates/create` → TemplateCreateView
- `/templates/:id` → TemplateDetailView
- `/ocr` → OcrListView
- `/ocr/new` → OcrUploadView
- `/ocr/:id` → OcrReviewView

Use nested routes under AppLayout for authenticated routes. `beforeEach` guard: if not authenticated and route != login → redirect `/login`.

### 9. Create AppLayout (`src/components/common/app-layout.vue`)
- `el-container` with `el-aside` (sidebar nav menu) + `el-main` (router-view)
- Menu items: Templates, OCR Jobs
- Logout button at bottom
- Sidebar collapse toggle

### 10. Create LoginView (`src/views/login-view.vue`)
- Centered card with el-form: username + password inputs
- Submit validates against env vars via auth store
- On success: router.push('/templates')
- On fail: el-message error

### 11. Create `src/main.ts`
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { VueQueryPlugin } from '@tanstack/vue-query'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.use(VueQueryPlugin)
app.mount('#app')
```

### 12. Create `src/App.vue`
Minimal: just `<router-view />`.

### 13. Verify
Run `npm run dev` — login page renders, auth guard works, layout shows after login.

## Todo List

- [ ] Init Vite project
- [ ] Install all deps
- [ ] Configure vite.config.ts (alias, port)
- [ ] Create .env with auth credentials
- [ ] Create env.d.ts type declarations
- [ ] Create auth.store.ts
- [ ] Create app.store.ts
- [ ] Create router/index.ts with all routes + guard
- [ ] Create app-layout.vue with sidebar nav
- [ ] Create login-view.vue
- [ ] Create main.ts with all plugins
- [ ] Create App.vue
- [ ] Create stub view files (empty components for routes)
- [ ] Verify dev server starts clean

## Success Criteria

- `npm run dev` starts without errors
- `/login` renders login form
- Invalid credentials show error message
- Valid credentials redirect to `/templates`
- Sidebar nav shows Templates and OCR links
- Unauthenticated access to any route redirects to `/login`
- Logout returns to `/login`

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Element Plus version conflict | Low | Pin version in package.json |
| Path alias not working | Low | Verify tsconfig paths match vite alias |

## Security Considerations

- Credentials in `.env` — acceptable for POC, add `.env` to `.gitignore`
- sessionStorage for auth — no JWT, fine for POC
- No XSS vectors since no user-generated content displayed raw

## Next Steps

- Phase 2: Data layer (types, services, mock API)
