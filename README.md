# CampusConnect

CampusConnect is a React and Django REST application for campus lost-and-found reports, private claims, potential matches, messaging, notifications, and moderation. The two requirements documents remain at the repository root; implementation lives in `frontend/` and `backend/`.

## Requirements

- Python 3.12 or later
- Node.js 20.19+ or 22.12+
- MySQL 8 for persistent MySQL development; SQLite is configured as the backend default for local evaluation

## Start the API

In PowerShell, from the repository root:

```powershell
py -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
.\backend\.venv\Scripts\python.exe backend\manage.py makemigrations accounts items matching claims communication moderation
.\backend\.venv\Scripts\python.exe backend\manage.py migrate
.\backend\.venv\Scripts\python.exe backend\manage.py seed_categories
.\backend\.venv\Scripts\python.exe backend\manage.py createsuperuser
.\backend\.venv\Scripts\python.exe backend\manage.py runserver
```

The API runs at `http://127.0.0.1:8000/api/`. The admin site is `http://127.0.0.1:8000/admin/`. For MySQL, update `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `backend/.env` after creating the database and user. Keep production secrets out of source control.

## Start the React app

Open a second terminal from the repository root:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Vite starts at `http://localhost:5173`. The frontend calls `http://localhost:8000/api` by default. Set `VITE_API_URL` in `frontend/.env.local` to use a different API URL. Before the API is available, Discover displays sample campus listings; private screens and forms use the live API.

## Verify

From the repository root:

```powershell
.\backend\.venv\Scripts\python.exe backend\manage.py check
.\backend\.venv\Scripts\python.exe backend\manage.py test tests.test_items
npm.cmd --prefix frontend run build
```

API implementation and routes are documented in [backend/README.md](backend/README.md).