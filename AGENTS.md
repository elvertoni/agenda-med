# Repository Guidelines

## Project Structure & Module Organization
This is a Django clinic scheduling project. The Django settings and root URLs live in `config/`. Domain apps are split by responsibility: `accounts/` for users and patient profiles, `professionals/` for specialties and professionals, `clinic_content/` for prices and public protocols, and `core/` for shared models, mixins, landing, dashboard, portal, and shared templates. App templates live under each app's `templates/` directory. Shared UI and layout templates are in `core/templates/components/` and `core/templates/layouts/`. Static assets are under `static/`, with Tailwind input/output in `static/css/`.

## Build, Test, and Development Commands
Use the project virtual environment when available:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Runs the local Django server.

```powershell
.\.venv\Scripts\python.exe manage.py check
```

Runs Django system checks.

```powershell
.\.venv\Scripts\python.exe manage.py test
```

Runs the Django test suite.

```powershell
.\.venv\Scripts\python.exe -m ruff check core config accounts professionals clinic_content manage.py
```

Runs lint checks.

```powershell
.\tailwindcss.exe -i .\static\css\input.css -o .\static\css\output.css
```

Rebuilds Tailwind CSS after template or class changes.

## Coding Style & Naming Conventions
Use Python 3.12+, 4-space indentation, and Django class-based views where the project already uses them. Ruff is configured in `pyproject.toml` with line length `100`, import sorting, and single quotes. Keep model, form, view, and URL names explicit, for example `ProfessionalListView`, `PatientProfile`, and `public_professionals`. Prefer project mixins such as `StaffRequiredMixin` and `PatientRequiredMixin` for access control.

## Testing Guidelines
Tests should use Django's built-in test framework and live in each app's `tests.py` or a `tests/` package if they grow. Name test classes by behavior, such as `DashboardAccessTests`, and test methods with `test_...`. Cover permissions, public page rendering, model constraints, and form validation when changing those areas.

## Commit & Pull Request Guidelines
No Git history is available in this workspace, so no existing commit convention can be inferred. Use concise imperative commit messages, for example `Add patient portal shell`. Pull requests should include a short summary, verification commands run, linked issue or sprint task, and screenshots for UI changes.

## Security & Configuration Tips
Do not commit real secrets, production databases, or patient data. Treat `db.sqlite3` as local development data. Keep authentication redirects and role restrictions aligned with the PRD: staff use email/password, while patient OTP access is planned for later sprints.
