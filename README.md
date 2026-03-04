# POC Shinhan - OCR Template System

A proof-of-concept OCR template management and document processing system. Create reusable document templates, annotate fields, and automatically extract data from images using OCR.

**Status:** POC Phase Complete (v1.0.0) | **Updated:** 2026-03-04

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.12+ (for backend development)

### Run with Docker Compose (Recommended)

```bash
# Start backend (FastAPI + SQLite)
docker-compose up

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` for the frontend and `http://localhost:8000/docs` for API docs.

### Run Locally (Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend (separate terminal):**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
poc-shinhan/
├── frontend/                # Vue 3 + TypeScript web app
│   ├── src/
│   │   ├── components/     # Reusable Vue components
│   │   ├── views/          # Page-level components
│   │   ├── services/       # Axios API layer
│   │   ├── stores/         # Pinia state management
│   │   ├── types/          # TypeScript interfaces
│   │   └── router/         # Vue Router configuration
│   └── package.json
│
├── backend/                 # FastAPI Python application
│   ├── app/
│   │   ├── main.py         # FastAPI initialization
│   │   ├── database.py     # SQLModel + SQLite setup
│   │   ├── models/         # Database models
│   │   ├── routers/        # API endpoints
│   │   └── services/       # Business logic
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/                    # Project documentation
│   ├── codebase-summary.md       # Complete codebase overview
│   ├── system-architecture.md    # Architecture & design
│   ├── code-standards.md         # Coding conventions
│   ├── project-overview-pdr.md   # Product requirements
│   ├── development-roadmap.md    # Feature roadmap
│   └── project-changelog.md      # Version history
│
├── plans/                   # Implementation plans & reports
├── docker-compose.yml       # Local dev setup
└── README.md               # This file
```

## Features

### Core Functionality (v1.0.0)
- **Template Management** - Create, edit, delete document templates
- **Field Annotations** - Visually annotate fields with bounding boxes
- **Template Versioning** - Multiple versions with activation control
- **Bundle Grouping** - Organize templates for batch processing
- **Mock OCR Processing** - Simulated field extraction (mock engine)
- **Image Upload** - Store template and document images
- **Interactive Editor** - Visual annotation canvas for field definition

### API Endpoints
See [`./docs/system-architecture.md`](./docs/system-architecture.md) for complete API documentation.

**Summary:**
- `GET/POST /api/templates` - Template CRUD
- `GET/POST /api/templates/{id}/versions` - Versioning
- `PUT /api/versions/{id}/fields` - Field annotations
- `GET/POST /api/bundles` - Bundle management
- `POST /api/ocr/process` - OCR processing
- `POST /api/images/upload` - Image uploads
- `GET /api/health` - Health check

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Vue 3, TypeScript, Vite, Tailwind CSS, Pinia |
| Backend | FastAPI, SQLModel, SQLite, Uvicorn |
| Container | Docker, Docker Compose |

## Documentation

Start with the docs directory:

| Document | Purpose |
|----------|---------|
| [codebase-summary.md](./docs/codebase-summary.md) | Overview of entire codebase |
| [system-architecture.md](./docs/system-architecture.md) | Architecture, data flow, design decisions |
| [code-standards.md](./docs/code-standards.md) | Naming conventions, code style, best practices |
| [project-overview-pdr.md](./docs/project-overview-pdr.md) | Product requirements and specifications |
| [development-roadmap.md](./docs/development-roadmap.md) | Feature roadmap and planned phases |
| [project-changelog.md](./docs/project-changelog.md) | Version history and changes |

## Development

### Frontend Development
```bash
cd frontend
npm install
npm run dev          # Start dev server with HMR
npm run build        # Build for production
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checks
```

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API docs at http://localhost:8000/docs
```

### Code Standards
Follow the conventions in [`./docs/code-standards.md`](./docs/code-standards.md):
- **Frontend:** kebab-case files, camelCase functions, PascalCase types
- **Backend:** snake_case files, PascalCase classes, snake_case functions
- Keep files under 200 lines
- Use TypeScript/Python type hints
- Add error handling and validation

### Testing
- Frontend: Manual browser testing (automated tests coming in v2.0)
- Backend: Use FastAPI Swagger UI at `http://localhost:8000/docs`

## Database

### SQLite (Current)
- **Location:** `backend/data/ocr.db` (auto-created on startup)
- **Tables:** template, templateversion, templatefield, bundle, bundleitem, ocrresult
- **Data Format:** ISO 8601 timestamps, UUID IDs, camelCase API responses

### Migration to PostgreSQL (Future - Phase 4)
Production deployments will use PostgreSQL. See [development-roadmap.md](./docs/development-roadmap.md) for timeline.

## Deployment

### Local Docker Compose
```bash
docker-compose up
# Backend: http://localhost:8000
# Frontend: npm run dev in separate terminal
```

### Production Deployment (Future)
See [development-roadmap.md](./docs/development-roadmap.md) Phase 4 for:
- PostgreSQL setup
- Kubernetes manifests
- Monitoring and logging
- Security hardening

## Known Limitations

- **No Authentication** - POC is single-user only (localhost)
- **Mock OCR** - Returns simulated field values (not real extraction)
- **SQLite Database** - Not suitable for production or multi-user
- **No Automated Tests** - Manual testing only
- **Local File Storage** - No cloud backup or CDN

See [project-changelog.md](./docs/project-changelog.md) for detailed notes.

## Roadmap

**Phase 1 (v1.0.0):** ✅ Complete
- Template CRUD, versioning, field annotations, bundles, mock OCR

**Phase 2 (v2.0.0):** In Planning (Apr-May 2026)
- Real OCR engine, confidence scores, batch processing

**Phase 3 (v2.5.0):** In Planning (May-Jun 2026)
- Authentication, authorization, multi-user support

**Phase 4 (v3.0.0):** In Planning (Jun-Aug 2026)
- PostgreSQL, comprehensive testing, monitoring, production-ready

**Phase 5 (v4.0.0):** In Planning (Jul-Sep 2026)
- Advanced features, webhooks, custom fields, mobile app

See [development-roadmap.md](./docs/development-roadmap.md) for details.

## Contributing

### Branch Strategy
- `main` - Production-ready code
- `develop` - Development integration branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches

### Before Committing
1. Follow code standards (see `./docs/code-standards.md`)
2. Test your changes manually
3. Run linting: `npm run lint` (frontend), `pylint` (backend)
4. Write clear commit messages (conventional commits)

### Pull Request Process
1. Create PR from feature branch to main
2. Code review required
3. Pass all checks
4. Merge when approved
5. Update CHANGELOG.md

## Troubleshooting

### Backend won't start
```bash
# Check Python version (need 3.12+)
python --version

# Check port 8000 is available
lsof -i :8000

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

### Frontend won't start
```bash
# Check Node version (need 18+)
node --version

# Clear node_modules cache
rm -rf node_modules package-lock.json
npm install
```

### Database issues
```bash
# Delete and recreate database
rm -rf backend/data/ocr.db
# Restart backend, it will create fresh database
```

### CORS errors
- Frontend must be at `http://localhost:5173`
- Backend CORS is configured in `backend/app/main.py`

## Support & Issues

### Report Issues
1. Check [GitHub Issues](https://github.com/shinhan-project/poc-shinhan/issues)
2. Create new issue with:
   - Description of problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots/logs if applicable

### Get Help
- Review documentation in `./docs/`
- Check API docs at `http://localhost:8000/docs`
- Review code examples in `./plans/` for implementation patterns

## License

[TBD - Add appropriate license]

## Version History

- **v1.0.0** (2026-03-04) - POC Phase Complete
  - Template CRUD, versioning, field annotations
  - Bundle management, mock OCR
  - FastAPI backend with SQLModel
  - Vue 3 frontend with Pinia
  - Docker containerization

See [project-changelog.md](./docs/project-changelog.md) for detailed changelog.
