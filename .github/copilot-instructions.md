# BrainForce AI Development Guidelines

This document provides essential context for AI agents working with the BrainForce codebase.

## Architecture Overview

BrainForce is a full-stack application with two main components:

1. **Backend (Python/FastAPI)**
   - Located in `/core/`
   - OpenAI-compatible API with memory, licensing, and logging capabilities
   - Key modules:
     - `main.py`: API server setup and routing
     - `api.py`: Core API endpoints
     - `memory.py`: Memory management
     - `logger.py`: Logging system
     - `mock.py`: Mock endpoints for testing

2. **Frontend (Next.js/React/TypeScript)**
   - Located in `/ui/`
   - Modern React application with TypeScript and Tailwind CSS
   - Key directories:
     - `pages/`: Next.js page components
     - `components/`: Reusable React components
     - `styles/`: Global styles and Tailwind configuration

## Development Workflow

### Backend
```bash
# Start the FastAPI server (development mode)
cd core
python main.py  # Runs on http://127.0.0.1:8000
```

### Frontend
```bash
# Start the Next.js development server
cd ui
npm run dev  # Runs on http://localhost:3000
```

## Project Structure

- `/core/`: Backend services and API
- `/ui/`: Frontend application
- `/docs/`: Documentation and AI engine components
- `/hub/`: Integration components (e.g., Google Drive)
- `/licenses/`: License management
- `/manifests/`: Configuration and role definitions
- `/status/`: Project status management and backup tools

## Key Integration Points

1. **API Communication**
   - Backend exposes REST endpoints at `/api`, `/memory`, `/logs`, and `/mock`
   - Frontend uses Axios for API calls (see `ui/pages/api.ts`)

2. **License Management**
   - License validation happens through `/licenses/validate.json`
   - Enterprise, Pro, and Lite tiers supported

3. **Role-Based Access**
   - Role definitions in `/manifests/roles.json`
   - Access control integrated with API endpoints

## Project-Specific Patterns

1. **Component Structure**
   - UI components follow atomic design principles
   - Common layout components in `ui/components/`
   - Page-specific components within respective page directories

2. **API Error Handling**
   - Backend uses FastAPI's built-in error handling
   - Frontend implements global error boundary in `_app.tsx`

3. **Configuration Management**
   - Environment-specific settings in manifest files
   - Role and version management through JSON manifests

## Common Tasks

1. **Adding New API Endpoints**
   - Create new route in appropriate module under `/core`
   - Add corresponding frontend API method in `ui/pages/api.ts`

2. **Creating UI Components**
   - Follow existing patterns in `ui/components`
   - Use Tailwind CSS for styling
   - Implement TypeScript interfaces for props

3. **License Validation**
   - Update rules in `/licenses/validate.json`
   - Test against different license tiers