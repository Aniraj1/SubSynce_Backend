# SubSync Backend

SubSync is a Django REST API for managing cleaning businesses.

The system manages:

- Users and roles
- Clients and cleaning sites
- Contractor assignments
- Cleaning schedules
- Completed cleaning work
- Contractor invoices
- Client invoices
- Revenue, expenditure, profit, and dashboards

## Requirements

- Python 3.12 or later
- Windows PowerShell
- Git

## Setup

Open PowerShell in the backend directory:

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

## Database

After activating the virtual environment, run:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Create a Django admin user when needed:

```powershell
python manage.py createsuperuser
```

## Run the API

```powershell
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.

## API Documentation

- Swagger UI: `http://127.0.0.1:8000/api/swagger/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`

## Main API Groups

- `/api/v1/admin/`
- `/api/v1/owner/`
- `/api/v1/user/`

Most endpoints require a JWT access token:

```text
Authorization: Bearer <access-token>
```

## Important Endpoints

### Contractor

- `/api/v1/user/schedule/` - View assigned schedules
- `/api/v1/user/clock-in/` - Start scheduled work
- `/api/v1/user/clock-out/<id>/` - Complete work
- `/api/v1/user/invoices/` - Submit and view contractor invoices
- `/api/v1/user/dashboard/` - View the contractor dashboard

### Administrator

- `/api/v1/admin/client/` - Manage clients
- `/api/v1/admin/site/` - Manage sites
- `/api/v1/admin/schedule/` - Manage schedules
- `/api/v1/admin/work/` - Review completed work
- `/api/v1/admin/invoices/` - Review contractor invoices
- `/api/v1/admin/client-invoice/` - Manage client invoices
- `/api/v1/admin/dashboard/` - View the administrator dashboard

Dashboard date filters use:

```text
?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
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
