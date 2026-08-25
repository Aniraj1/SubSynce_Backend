# SubSync Backend

Django REST API for the SubSync project.

## Requirements

- Python 3.12 or later
- Windows PowerShell
- Git

## Installation

Open PowerShell in the project directory:

```powershell
cd "C:\path\to\backend"

python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run this for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

## Environment Configuration

The project reads configuration from `.env` through `python-decouple`. Create a `.env` file in the project root if one does not exist.

Required settings include:

```env
DEBUG=True
SECRET_KEY=replace-with-a-long-random-secret
JWT_ACCESS_TOKEN_LIFETIME_HRS=4
JWT_REFRESH_TOKEN_LIFETIME_HRS=48
JWT_KEY=replace-with-a-long-random-jwt-key
PASSWORD_MIN_LENGTH=8
THROTTLE_RATES_IN_DAYS=1000000
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

Do not use development secrets in production. Keep real secrets out of source control.

## Database Setup

After activating the virtual environment:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Create a Django admin user when needed:

```powershell
python manage.py createsuperuser
```

## Run the Server

```powershell
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.

## API Documentation

- Swagger UI: `http://127.0.0.1:8000/api/swagger/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`

## API Route Groups

- `/api/v1/admin/`
- `/api/v1/owner/`
- `/api/v1/user/`

Authentication uses JWT access and refresh tokens. Send an access token to protected endpoints with:

```text
Authorization: Bearer <access-token>
```

## User Roles

The application supports these roles:

- `OWNER`
- `ADMINISTRATOR`
- `CONTRACTOR`

Role permissions are enforced by the API. An owner can create administrators or contractors. An administrator can create contractors. Contractors cannot create accounts.

## Common Commands

```powershell
python manage.py test
python manage.py showmigrations
python manage.py spectacular --validate
```
