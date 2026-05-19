# GEMINI.md - Kanara Tunnel Manager (KTM)

This file provides context and instructions for AI agents working on the Kanara Tunnel Manager project.

## Project Overview

**Kanara Tunnel Manager (KTM)** is a modern web-based interface for managing [FRP (Fast Reverse Proxy)](https://github.com/fatedier/frp) tunnels. It allows administrators and users to create, monitor, and manage remote access and NAT traversal tunnels through a clean dashboard.

### Core Architecture
- **Backend:** Python 3.10+ using **Flask**.
- **Database:** **PostgreSQL** (primary) with **Redis** (caching).
- **Frontend:** **Astro** with **React**, **Radix UI**, and **Tailwind CSS**. The frontend is built into static files (`frontend/dist`) and served by the Flask backend.
- **Client Agent:** A Python-based agent (`lib/ktmc.py`) that runs on client machines, automatically fetches tunnel configurations from the server, and manages the local `frpc` process.
- **FRP Integration:** Manages `frps` (server) and `frpc` (client) binaries.

## Directory Structure

- `app/`: Flask application package (models, routes, auth, email, etc.).
- `frontend/`: Astro/React source code.
- `lib/`: Shared libraries, client agent (`ktmc.py`), and installer templates.
- `bin/`: Binaries for FRP and local configuration.
- `data/`: Local storage for profile photos and other persistent data.
- `scripts/`: Utility scripts (e.g., `create_user.py`).
- `frp/`: FRP server/client binaries and default TOML configs.

## Getting Started

### Backend Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your environment variables.
4. Run the application:
   ```bash
   python ktm.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Build for production (required for Flask to serve the UI):
   ```bash
   npm run build
   ```
4. For development with HMR:
   ```bash
   npm run dev
   ```

### Docker
The project can be run entirely via Docker:
```bash
docker-compose up --build
```

## Development Conventions

### Backend (Python/Flask)
- Follow **PEP 8** style guidelines.
- Use **SQLAlchemy** for database interactions.
- API endpoints should return JSON and follow RESTful principles where possible.
- New routes should be added to `app/routes.py` (or a relevant blueprint).

### Frontend (Astro/React)
- Use **Radix UI** primitives for accessible components.
- Style with **Tailwind CSS**.
- Prefer functional components and hooks in React.
- Ensure the frontend build is updated (`npm run build`) after making changes if testing via the Flask server.

### Client Agent
- The installer script (`lib/installer_template.sh`) is used to deploy the agent on Linux machines.
- The agent (`lib/ktmc.py`) communicates with the server via the `/api/<client_id>/kana_frpc.json` endpoint.

## Key Files
- `ktm.py`: Main entry point for the Flask application.
- `config.py`: Configuration class handling environment variables.
- `app/models.py`: Database schema definitions.
- `app/routes.py`: Main API and routing logic.
- `frontend/src/pages/`: Astro pages defining the UI structure.
- `lib/ktmc.py`: The client-side tunnel management agent.

## TODO / Future Improvements
- [ ] Add automated test suite (unit and integration tests).
- [ ] Implement more granular Role-Based Access Control (RBAC).
- [ ] Add real-time tunnel status monitoring via WebSockets or polling.
- [ ] Improve documentation for multi-tenancy support.
