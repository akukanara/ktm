# Repository Guidelines

## Project Structure & Module Organization
This repository is a Flask-based tunnel manager.
- `ktm.py`: local entrypoint; creates tables and starts the web app.
- `app/`: application package (`routes.py`, `auth.py`, `admin.py`, `models.py`, `forms.py`, `frps.py`).
- `app/templates/`: Jinja2 templates for dashboard, auth, admin, and profile views.
- `lib/` and `bin/frp/`: helper scripts and FRP binaries/config artifacts.
- `config.py`: runtime configuration (database, FRP, upload, mail).
- `data/profile/photos/`: local profile image storage.

Keep new feature code inside `app/` and group by concern (routes, auth, models, templates).

## Build, Test, and Development Commands
Use the project virtual environment and run from repo root.
- `python3 -m venv venv && source venv/bin/activate`: create/activate environment.
- `pip install -r requirements.txt`: install dependencies.
- `python ktm.py`: run the app on `0.0.0.0:5000` with debug enabled.
- `python3 -m py_compile ktm.py app/*.py`: quick syntax check before opening a PR.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation.
- Use `snake_case` for functions/variables, `PascalCase` for classes, and lowercase module names.
- Keep Flask blueprints focused by domain (`auth`, `admin`, `main`) and avoid large mixed-purpose route files.
- Prefer explicit imports and short, readable functions over deeply nested handlers.

## Testing Guidelines
There is no dedicated automated test suite yet (`tests/` is not present).
- For now, run `python3 -m py_compile ktm.py app/*.py` and manually validate key flows: login, client creation, tunnel generation, and FRPS startup.
- When adding tests, create a `tests/` directory and name files `test_<feature>.py`.

## Commit & Pull Request Guidelines
Current history uses short imperative subjects (for example: `Update config.py`, `Update README.md`).
- Commit format: `<Verb> <scope>` with concise subject lines under ~72 chars.
- PRs should include: purpose, summary of changes, manual test steps, and screenshots for template/UI updates.
- Link related issues and call out config or migration impact explicitly.

## Security & Configuration Tips
- Do not commit real secrets in `config.py` (DB URI, SMTP credentials, FRP token, S3 keys).
- Prefer environment variables for sensitive values.
- Treat `bin/frp/config/*.log` and `*.pid` as runtime artifacts; avoid including generated operational data in commits.
