# SubSync Backend

SubSync is a Django REST API for cleaning businesses. It manages users, clients,
sites, schedules, completed work, invoices, and dashboards.

## Requirements

- Python 3.12 or newer
- PowerShell on Windows
- `virtualenv`

## Setup

Run these commands from the project `backend` directory:

```powershell
python -m pip install --upgrade pip virtualenv
virtualenv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

After activation, your PowerShell prompt should show `(venv)`.

## Environment

Copy `sample.env` to `.env` and fill in the secret values:

```powershell
Copy-Item sample.env .env
```

At minimum, set these values in `.env`:

```env
DEBUG=True
SECRET_KEY=your-secret-key
JWT_KEY=your-jwt-key
SUPER_ADMIN_PASSWORD=your-password
```

Keep `.env` private and do not commit real secrets.

## Database

```powershell
python manage.py check
python manage.py migrate
```

Create an owner account for administration:

```powershell
python manage.py createsuperuser
```

Superusers are created with the `OWNER` role.

## Run the API

```powershell
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000/`.

## API Documentation

- Swagger: `http://127.0.0.1:8000/api/swagger/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## API Groups

```text
/api/v1/owner/
/api/v1/admin/
/api/v1/user/
```

Most endpoints require a JWT access token:

```text
Authorization: Bearer <access-token>
```

## Roles

- `OWNER`: creates administrators and contractors.
- `ADMINISTRATOR`: manages clients, sites, schedules, work, and invoices.
- `CONTRACTOR`: views assigned work, clocks in and out, and manages contractor invoices.

## Common Commands

Run all tests:

```powershell
python -m pytest
```

Run one test:

```powershell
python -m pytest -k test_name -s
```

Other useful commands:

```powershell
python manage.py showmigrations
python manage.py spectacular --validate
```
