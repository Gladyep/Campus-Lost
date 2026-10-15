# CampusConnect backend

Django REST API for the CampusConnect campus lost-and-found application. It includes email accounts, item reports and images, potential matches, claim verification, private conversations, notifications, user reports, and administrator review endpoints.

## Local setup

Python 3.12 or later is required. From this directory, create a virtual environment and install dependencies:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The default database is SQLite so the API and tests can run without a local database server. To use MySQL, create a database and user with `utf8mb4`, then set `DB_ENGINE=mysql` and the matching credentials in `.env`. Never commit `.env` or production secrets.

Create the schema, seed the standard categories, and start the API:

```powershell
.venv\Scripts\python.exe manage.py makemigrations accounts items matching claims communication moderation
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_categories
.venv\Scripts\python.exe manage.py createsuperuser
.venv\Scripts\python.exe manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/`. Admin is at `/admin/`. Set `VITE_API_URL` in the frontend environment to change the API base URL.

## Main endpoints

- `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/refresh/`, `GET/PATCH /api/auth/profile/`
- `GET/POST /api/items/`, `GET/PATCH/DELETE /api/items/{id}/`, `GET /api/categories/`
- `POST /api/visual-search/` (authenticated multipart image search)
- `GET /api/matches/`, `POST /api/claims/`, `POST /api/claims/{id}/answers/`, `PATCH /api/claims/{id}/decision/`
- `GET/POST /api/conversations/`, `GET/POST /api/conversations/{id}/messages/`, `GET/PATCH /api/notifications/`
- `POST /api/reports/`, `GET /api/admin/dashboard/`, `GET /api/admin/flagged-claims/`

Item list filters include `search`, `item_type`, `category_name`, `location`, `date_after`, `date_before`, `status`, and `mine=true`. List endpoints are paginated. Matching is advisory and never approves a claim.

## Visual search

Send an authenticated `multipart/form-data` request to `/api/visual-search/` with an `image` field. Optional `category`, `location`, and `event_date` fields filter eligible found-item reports. The API rejects files over 5 MB, unsupported formats, and images larger than 4096 pixels per side or 16 megapixels. Results contain public item-report fields only and are ranked by approximate visual similarity.

The current Pillow-based baseline compares small spatial RGB samples, color histograms, and a difference hash. It processes up to the 250 most recently reported eligible found items with photos and returns at most 20 results. It is not a pretrained AI model and similarity is not proof of ownership. Features are computed at request time; no schema migration or additional dependency is required.

## Checks

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test tests.test_items
```