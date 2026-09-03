# SubSync Backend - Comprehensive Documentation

## Phase Status: Login & Authentication System (Merged)

**Branch:** `merging_login`  
**Date:** September 2026  
**Status:** ✅ Complete and Tested

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Decision: Hybrid Approach](#architecture-decision)
3. [Phase 1: What We Built](#phase-1-what-we-built)
4. [File Structure & Purpose](#file-structure)
5. [Detailed File-by-File Explanation](#file-explanations)
6. [Setup Instructions](#setup)
7. [Testing the Login System](#testing)
8. [Change Log](#change-log)
9. [References](#references)
10. [Next Phases](#next-phases)

---

## 🎯 Project Overview

**SubSync** is a cleaning management platform that connects:
- **Owners** (business owners)
- **Administrators** (managers)
- **Contractors/Subcontractors** (cleaning workers)

**Core Features:**
- Client and Site management
- Schedule and job tracking
- Invoice generation and payment tracking
- Compliance document management
- Profitability reporting

**Current Phase:** User authentication (login/logout) with session-based web interface

---

## 🏗️ Architecture Decision: Why Hybrid Approach?

### The Problem

We had **two conflicting specifications**:

1. **GitHub Backend** (existing code):
   - Django REST Framework (DRF) with JWT tokens
   - Multi-app structure (`authuser`, `client`)
   - API-first design (JSON responses)
   - Built for mobile/future React SPA

2. **techstack.md** (project requirements):
   - Django templates with Tailwind CSS
   - Session-based authentication
   - Single `ops` app
   - Server-rendered HTML

### The Solution: Option C (Hybrid)

We chose to **keep the existing GitHub backend** AND **add a new template layer** alongside it.

**Why?**
- ✅ Preserves all existing API code (no breaking changes)
- ✅ Matches techstack.md for web frontend
- ✅ Enables both web and mobile access
- ✅ Future-proof (can add React SPA later)

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    Browser / Mobile                      │
─────────────────────┬───────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼────┐              ┌─────▼────┐
    │  Web    │              │   API    │
    │ (ops)   │              │ (DRF)    │
    │         │              │          │
    │ Session │              │   JWT    │
    │  Auth   │              │  Auth    │
    │         │              │          │
    │ HTML    │              │  JSON    │
    │Response │              │ Response │
    └────┬────              └─────┬────
         │                         │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │    Django Core          │
         │    (settings.py)        │
         │                         │
         │  AUTH_USER_MODEL =      │
         │  'authuser.User'        │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │      Database           │
         │    (db.sqlite3)         │
         │                         │
         │  POC_USER               │
         │  POC_CLIENT             │
         │  POC_SITE               │
         └─────────────────────────
```

**Key Insight:** Both `ops` (web) and `authuser`/`client` (API) share:
- The same database
- The same User model
- The same authentication system
- Different response formats (HTML vs JSON)

---

##  Phase 1: What We Built

### Features Implemented

1. ✅ **Login Page** (`/`)
   - Username/password form
   - Session-based authentication
   - Error handling with messages
   - Demo credentials display

2. ✅ **Dashboard** (`/dashboard/`)
   - Role-based navigation (Owner/Admin/Contractor see different menus)
   - Stats cards (active jobs, subcontractors, invoices, revenue)
   - User profile display
   - Logout button

3. ✅ **Logout** (`/logout/`)
   - Session termination
   - Redirect to login
   - Success message

4. ✅ **Authentication Flow**
   - `@login_required` decorator protects dashboard
   - Automatic redirect to login if not authenticated
   - Session cookies for persistence
   - CSRF protection on all forms

5. ✅ **Design System**
   - Tailwind CSS with SubSync brand colors
   - Material Symbols icons
   - Pretendard font
   - Responsive layout

---

## 📁 File Structure

```
SubSynce_Backend/
│
├── core/                          # Project configuration
│   ├── settings.py                # ← MODIFIED: Added ops app, templates, static, auth settings
│   └── urls.py                    # ← MODIFIED: Added web frontend URLs
│
├── authuser/                      # Existing API app (UNCHANGED)
│   ├── api/
│   │   ├── views/                 # API views (return JSON)
│   │   ── urls/                  # API routes (/api/v1/...)
│   ├── model/
│   │   └── user.py                # User model definition
│   └── models.py                  # Exports User model
│
├── client/                        # Existing API app (UNCHANGED)
│   ├── api/
│   │   ├── views/                 # API views (return JSON)
│   │   └── urls/                  # API routes
│   └── model/
│       └── clientmanage.py        # Client & Site models
│
├── ops/                           # ← NEW: Web template app
│   ├── __init__.py                # Makes ops a Python package
│   ├── admin.py                   # Django admin (empty for now)
│   ├── apps.py                    # App configuration
│   ├── models.py                  # Models (empty, uses authuser.User)
│   ├── tests.py                   # Tests (empty for now)
│   ├── views.py                   # ← NEW: Login, logout, dashboard views
│   ├── urls.py                    # ← NEW: URL routes for web pages
│   ├── migrations/
│   │   └── __init__.py            # Migrations folder
│   ├── templates/
│   │   ├── base.html              # ← NEW: Base template (shared layout)
│   │   └── ops/
│   │       ├── login.html         # ← NEW: Login page
│   │       └── dashboard.html     # ← NEW: Dashboard page
│   └── static/
│       └── css/
│           └── app.css            # ← NEW: Custom CSS styles
│
├── manage.py                      # Django command center
├── requirements.txt               # Python packages
└── README.md                      # ← THIS FILE (updated)
```

---

## 📝 Detailed File-by-File Explanation

### 1. **`core/settings.py`** (MODIFIED)

**Why Modified:** To integrate the new `ops` app with the existing project.

**Changes Made:**

#### a) Added `ops` to `INSTALLED_APPS`
```python
INSTALLED_APPS = [
    ...
    'authuser',
    'client',
    'ops',  # ← ADDED
]
```
**Why:** Django needs to know about the `ops` app to use its views, templates, and static files.

#### b) Updated `TEMPLATES` setting
```python
TEMPLATES = [
    {
        'DIRS': [BASE_DIR / 'ops' / 'templates'],  # ← ADDED
        ...
    },
]
```
**Why:** Tells Django where to find HTML templates. Without this, Django can't find `login.html` or `dashboard.html`.

#### c) Added `STATICFILES_DIRS`
```python
STATICFILES_DIRS = [
    BASE_DIR / 'ops' / 'static',  # ← ADDED
]
```
**Why:** Tells Django where to find CSS files. Without this, `app.css` won't load.

#### d) Added Authentication Settings
```python
LOGIN_URL = 'ops:login'                    # ← ADDED
LOGIN_REDIRECT_URL = 'ops:dashboard'       # ← ADDED
LOGOUT_REDIRECT_URL = 'ops:login'          # ← ADDED
```
**Why:**
- `LOGIN_URL`: Where to redirect unauthenticated users (when `@login_required` is used)
- `LOGIN_REDIRECT_URL`: Where to redirect after successful login
- `LOGOUT_REDIRECT_URL`: Where to redirect after logout

---

### 2. **`core/urls.py`** (MODIFIED)

**Why Modified:** To route web requests to the `ops` app.

**Changes Made:**

```python
# BEFORE:
basepatterns = [
    path("api/schema/", ...),
    path("api/", include("authuser.urls")),
    path("api/", include("client.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(basepatterns)),
]
```

```python
# AFTER:
# Web frontend URLs (template-based views)
web_patterns = [
    path("", include("ops.urls")),  # ← ADDED
]

# API URLs (DRF views)
api_patterns = [
    path("api/schema/", ...),
    path("api/", include("authuser.urls")),
    path("api/", include("client.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(web_patterns)),    # ← ADDED: Web routes
    path("", include(api_patterns)),    # ← KEPT: API routes
]
```

**Why:** 
- Web URLs (like `/dashboard/`) are handled by `ops.urls`
- API URLs (like `/api/v1/user/login/`) are handled by `authuser.urls`
- Both can coexist without conflicts

---

### 3. **`ops/__init__.py`** (NEW - EMPTY FILE)

**Why Created:** Makes `ops` a Python package.

**What It Does:**
- Empty file (no code)
- Tells Python "this folder is a module that can be imported"
- Required by Django to recognize the app

**Analogy:** Like a sign on a door that says "This is an office, not a storage room"

---

### 4. **`ops/apps.py`** (NEW)

**Why Created:** Registers the app with Django.

**Content:**
```python
from django.apps import AppConfig

class OpsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ops'
```

**What It Does:**
- `name = 'ops'` - Tells Django "my app name is ops"
- `default_auto_field` - Specifies the default primary key type for models

**Why Needed:** Django uses this to load the app and its components.

---

### 5. **`ops/admin.py`** (NEW - EMPTY)

**Why Created:** Required by Django app structure.

**Content:**
```python
from django.contrib import admin
# Register your models here.
```

**What It Does:**
- Empty for now (we don't have models in `ops` yet)
- Will be used later to register models for Django admin panel

**Why Needed:** Django expects this file in every app.

---

### 6. **`ops/models.py`** (NEW - EMPTY)

**Why Created:** Required by Django app structure.

**Content:**
```python
from django.db import models
# Create your models here.
```

**What It Does:**
- Empty for now (we use `authuser.User` model instead)
- Will be used later if we need app-specific models

**Why Needed:** Django expects this file in every app.

---

### 7. **`ops/tests.py`** (NEW - EMPTY)

**Why Created:** Required by Django app structure.

**Content:**
```python
from django.test import TestCase
# Create your tests here.
```

**What It Does:**
- Empty for now
- Will be used to write tests for views

**Why Needed:** Django expects this file in every app.

---

### 8. **`ops/views.py`** (NEW)

**Why Created:** Contains the logic for login, logout, and dashboard.

**Content:**
```python
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def login_view(request):
    """
    Login view - handles user authentication with Django sessions
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('ops:dashboard')
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user against the database
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful - create session
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to dashboard
            next_url = request.GET.get('next', 'ops:dashboard')
            return redirect(next_url)
        else:
            # Login failed
            messages.error(request, 'Invalid username or password.')
    
    # Handle GET request (show login form)
    return render(request, 'ops/login.html')


def logout_view(request):
    """
    Logout view - ends user session and redirects to login
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('ops:login')


@login_required
def dashboard_view(request):
    """
    Dashboard view - shows overview of the system
    Only authenticated users can access this page
    """
    context = {
        'user': request.user,
        'stats': {
            'active_jobs': 12,
            'subcontractors': 28,
            'invoices': 45,
            'revenue': 124500,
        }
    }
    
    return render(request, 'ops/dashboard.html', context)
```

**What Each Function Does:**

#### `login_view(request)`
- **Purpose:** Handles login form display and processing
- **GET request:** Shows the login form (`login.html`)
- **POST request:** 
  1. Gets username and password from form
  2. Calls `authenticate()` to check credentials against database
  3. If correct: Creates session, redirects to dashboard
  4. If wrong: Shows error message
- **Already logged in:** Redirects to dashboard (prevents re-login)

**Why Uses `authenticate()`:** This function uses `authuser.User` model automatically (because of `AUTH_USER_MODEL` setting in `settings.py`)

#### `logout_view(request)`
- **Purpose:** Ends user session
- **What it does:**
  1. Calls `logout()` to clear session
  2. Shows success message
  3. Redirects to login page

#### `dashboard_view(request)`
- **Purpose:** Shows the main dashboard
- **`@login_required` decorator:** Ensures only logged-in users can access
- **What it does:**
  1. Gets user info from `request.user` (this is `authuser.User` object)
  2. Creates context data (mock stats for now)
  3. Renders `dashboard.html` with context

**Why Uses `@login_required`:** Protects the page. If user is not logged in, Django automatically redirects to `LOGIN_URL` (which is `ops:login`)

---

### 9. **`ops/urls.py`** (NEW)

**Why Created:** Maps URLs to view functions.

**Content:**
```python
from django.urls import path
from . import views

# App namespace
app_name = 'ops'

urlpatterns = [
    # Login page (root URL)
    path('', views.login_view, name='login'),
    
    # Dashboard (protected - requires login)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Logout
    path('logout/', views.logout_view, name='logout'),
]
```

**What Each URL Does:**

| URL | View | Name | Purpose |
|---|---|---|---|
| `/` | `login_view` | `login` | Shows login form |
| `/dashboard/` | `dashboard_view` | `dashboard` | Shows dashboard (protected) |
| `/logout/` | `logout_view` | `logout` | Logs user out |

**Why `app_name = 'ops'`:** 
- Creates a namespace for URL names
- Allows us to use `{% url 'ops:login' %}` in templates
- Prevents naming conflicts with other apps

**How Templates Use This:**
```html
<a href="{% url 'ops:login' %}">Login</a>
<a href="{% url 'ops:dashboard' %}">Dashboard</a>
<a href="{% url 'ops:logout' %}">Logout</a>
```

---

### 10. **`ops/migrations/__init__.py`** (NEW - EMPTY FILE)

**Why Created:** Makes `migrations` a Python package.

**What It Does:**
- Empty file
- Tells Django this folder contains migration files
- Required for Django to track database changes

**Why Needed:** Even if we don't have models yet, Django expects this folder.

---

### 11. **`ops/templates/base.html`** (NEW)

**Why Created:** Shared layout for all pages.

**Content:** (Full HTML with Tailwind CSS config, fonts, messages area, and `{% block %}` tags)

**What It Does:**

#### a) **HTML Head Section**
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SubSync{% endblock %}</title>
    
    <!-- Fonts -->
    <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/..." rel="stylesheet">
    
    <!-- Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined..." rel="stylesheet">
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Tailwind Config -->
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        surface: '#F5F3F1',
                        primary: '#F4842B',
                        ...
                    }
                }
            }
        }
    </script>
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{% static 'css/app.css' %}">
</head>
```

**Why This Section:**
- Loads Pretendard font (from design.md)
- Loads Material Symbols icons (from design.md)
- Loads Tailwind CSS (for styling)
- Configures Tailwind with SubSync brand colors
- Loads custom CSS for icon styling

#### b) **Body Section**
```html
<body class="bg-surface text-ink font-sans min-h-screen">
    
    <!-- Messages Area -->
    {% if messages %}
    <div class="fixed top-4 right-4 z-50 space-y-2">
        {% for message in messages %}
        <div class="px-4 py-3 rounded-xl shadow-lg ...">
            {{ message }}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Main Content -->
    {% block content %}
    {% endblock %}
    
    <!-- Auto-hide messages -->
    <script>...</script>
</body>
```

**Why This Section:**
- `bg-surface text-ink` - Applies brand colors
- `{% if messages %}` - Shows success/error messages from views
- `{% block content %}` - Placeholder for child templates to fill
- JavaScript - Auto-hides messages after 5 seconds

**How Child Templates Use It:**
```html
{% extends 'base.html' %}

{% block title %}Login - SubSync{% endblock %}

{% block content %}
    <!-- Your page content here -->
{% endblock %}
```

---

### 12. **`ops/templates/ops/login.html`** (NEW)

**Why Created:** The login page that users see.

**Content:** (Full HTML with login form)

**What It Does:**

#### a) **Template Inheritance**
```html
{% extends 'base.html' %}
```
**Why:** Inherits the base layout (fonts, styles, messages area)

#### b) **Title Block**
```html
{% block title %}Login - SubSync{% endblock %}
```
**Why:** Sets the page title (shown in browser tab)

#### c) **Content Block**
```html
{% block content %}
<div class="min-h-screen flex items-center justify-center px-4 py-12">
    ...
</div>
{% endblock %}
```
**Why:** Fills in the main content area of `base.html`

#### d) **Login Form**
```html
<form method="post" action="{% url 'ops:login' %}" class="space-y-5">
    {% csrf_token %}
    
    <input type="text" name="username" required>
    <input type="password" name="password" required>
    
    <button type="submit">Sign In</button>
</form>
```

**Why Each Part:**

- **`method="post"`**: Sends data securely (not in URL)
- **`action="{% url 'ops:login' %}"`**: Sends to login view
- **`{% csrf_token %}`**: Security token (prevents CSRF attacks)
- **`name="username"`**: Must match what `login_view` expects (`request.POST.get('username')`)
- **`name="password"`**: Must match what `login_view` expects (`request.POST.get('password')`)
- **`required`**: HTML5 validation (field must be filled)

#### e) **Demo Credentials Display**
```html
<div class="mt-6 pt-6 border-t border-surface-container">
    <p class="text-xs text-ink-light text-center mb-3">Demo Credentials:</p>
    <div class="space-y-2 text-xs">
        <div class="flex justify-between items-center p-2 rounded-lg bg-surface">
            <span class="text-ink-light">Owner:</span>
            <code class="text-ink font-mono">testowner / Test@12345</code>
        </div>
        ...
    </div>
</div>
```
**Why:** Shows test credentials for easy login during development

---

### 13. **`ops/templates/ops/dashboard.html`** (NEW)

**Why Created:** The main dashboard page after login.

**Content:** (Full HTML with stats cards and logout button)

**What It Does:**

#### a) **Template Inheritance**
```html
{% extends 'base.html' %}
```
**Why:** Inherits base layout

#### b) **Header with Logout**
```html
<div class="flex justify-between items-center mb-8">
    <div>
        <h1 class="text-3xl font-bold text-ink">
            Welcome, {{ user.username }}! 👋
        </h1>
        <p class="text-ink-light mt-2">Role: {{ user.role }}</p>
    </div>
    <a href="{% url 'ops:logout' %}" 
       class="bg-primary text-on-primary px-4 py-2 rounded-xl hover:bg-primary-hover transition-colors flex items-center gap-2">
        <span class="material-symbols-outlined">logout</span>
        Logout
    </a>
</div>
```

**Why Each Part:**

- **`{{ user.username }}`**: Displays username from `authuser.User` model
- **`{{ user.role }}`**: Displays role (OWNER, ADMINISTRATOR, CONTRACTOR)
- **`{% url 'ops:logout' %}`**: Link to logout view
- **`bg-primary text-on-primary`**: Orange button with white text (SubSync brand)
- **`material-symbols-outlined`**: Logout icon from Material Symbols

#### c) **Stats Grid**
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <!-- Active Jobs -->
    <div class="bg-white rounded-2xl p-6 border border-surface-container">
        <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <span class="material-symbols-outlined text-primary">work</span>
            </div>
        </div>
        <p class="text-3xl font-bold text-ink">{{ stats.active_jobs }}</p>
        <p class="text-sm text-ink-light mt-1">Active Jobs</p>
    </div>
    ...
</div>
```

**Why Each Part:**

- **`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4`**: Responsive grid (1 column on mobile, 2 on tablet, 4 on desktop)
- **`bg-white rounded-2xl p-6 border border-surface-container`**: White card with rounded corners and border
- **`{{ stats.active_jobs }}`**: Displays number from context (currently mock data)
- **`material-symbols-outlined`**: Icon (work, person, receipt_long, trending_up)

#### d) **Context Data**
The template receives this data from `dashboard_view`:
```python
context = {
    'user': request.user,  # authuser.User object
    'stats': {
        'active_jobs': 12,
        'subcontractors': 28,
        'invoices': 45,
        'revenue': 124500,
    }
}
```

**Why:** Template uses `{{ stats.active_jobs }}` to display the number

---

### 14. **`ops/static/css/app.css`** (NEW)

**Why Created:** Custom CSS for icons and scrollbar styling.

**Content:**
```css
/* Material Symbols styling */
.material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    line-height: 1;
    ...
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #F5F3F1;
}

::-webkit-scrollbar-thumb {
    background: #D9D3CC;
    border-radius: 4px;
}
```

**What It Does:**

#### a) **Material Symbols Styling**
- Sets font family to Material Symbols
- Defines default size (24px)
- Ensures icons render correctly

**Why Needed:** Without this, Material Symbols icons won't display properly

#### b) **Custom Scrollbar**
- Styles the scrollbar to match SubSync design
- Uses brand colors (#F5F3F1 for track, #D9D3CC for thumb)

**Why Needed:** Default browser scrollbars don't match the design

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11 or 3.12
- Git
- VS Code (recommended)
- Internet connection (for Tailwind CDN)

### Step 1: Clone the Repository

```bash
git clone https://github.com/aayushRauniyar/SubSynce_Backend.git
cd SubSynce_Backend
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**You'll know it worked when** you see `(venv)` at the start of your terminal line.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**What this installs:**
- Django 5.2.9 (downgraded from 6.0.3 for Python 3.11 compatibility)
- Django REST Framework
- SimpleJWT
- django-cors-headers
- drf-spectacular
- python-decouple
- And more...

### Step 4: Create `.env` File

Create a file named `.env` in the project root:

```env
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_LIFETIME_HRS=4
JWT_REFRESH_TOKEN_LIFETIME_HRS=48
JWT_KEY=your-jwt-secret-key-change-this
PASSWORD_MIN_LENGTH=8
THROTTLE_RATES_IN_DAYS=1000000
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

**Why Each Variable:**

- **`DEBUG=True`**: Shows detailed error messages (ONLY for development)
- **`SECRET_KEY`**: Master password for Django (NEVER share in production)
- **`JWT_ACCESS_TOKEN_LIFETIME_HRS`**: How long access tokens last (4 hours)
- **`JWT_REFRESH_TOKEN_LIFETIME_HRS`**: How long refresh tokens last (48 hours)
- **`JWT_KEY`**: Secret key for signing JWT tokens
- **`PASSWORD_MIN_LENGTH`**: Minimum password length (8 characters)
- **`THROTTLE_RATES_IN_DAYS`**: API rate limiting (1000000 requests per day = unlimited)
- **`DB_ENGINE`**: Database type (SQLite for development)
- **`DB_NAME`**: Database file name

### Step 5: Run Migrations

```bash
python manage.py migrate
```

**What this does:**
- Creates `db.sqlite3` file (the database)
- Creates tables for all models (User, Client, Site, etc.)
- Applies all migrations

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, authuser, client, contenttypes, sessions, token_blacklist
Running migrations:
  Applying authuser.0001_initial... OK
  Applying authuser.0002_alter_user_role... OK
  ...
```

### Step 6: Create Test Users

Open Django shell:
```bash
python manage.py shell
```

In the Python shell, type:
```python
from authuser.models import User

# Create owner user
user = User.objects.create_user(
    username='testowner',
    email='owner@test.com',
    password='Test@12345',
    role='OWNER'
)
print(f"Created: {user.username}, Role: {user.role}")

# Create admin user
admin = User.objects.create_user(
    username='admin1',
    email='admin@test.com',
    password='Test@12345',
    role='ADMINISTRATOR'
)
print(f"Created: {admin.username}, Role: {admin.role}")

# Create contractor user
contractor = User.objects.create_user(
    username='contractor1',
    email='contractor@test.com',
    password='Test@12345',
    role='CONTRACTOR'
)
print(f"Created: {contractor.username}, Role: {contractor.role}")

# Exit shell
exit()
```

**Why These Users:**
- **testowner**: Full access to all features
- **admin1**: Management access (can't create users)
- **contractor1**: Limited access (own data only)

### Step 7: Start the Server

```bash
python manage.py runserver
```

**Expected output:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
September 03, 2026 - 12:00:00
Django version 5.2.9, using settings 'core.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Step 8: Test the Login

1. Open browser to: `http://127.0.0.1:8000/`
2. You should see the **Login Page** with orange styling
3. Enter credentials:
   - Username: `testowner`
   - Password: `Test@12345`
4. Click "Sign In"
5. You should be redirected to the **Dashboard**
6. Try the other users too (admin1, contractor1)
7. Click "Logout" button
8. You should be redirected back to login

### Step 9: Test Protected Routes

1. Logout
2. Try to access: `http://127.0.0.1:8000/dashboard/`
3. You should be **automatically redirected** to login page
4. Login again
5. Now you can access the dashboard

---

## 🧪 Testing the Login System

### Test Cases

#### ✅ Test 1: Successful Login
1. Visit `http://127.0.0.1:8000/`
2. Enter valid credentials (testowner / Test@12345)
3. Click "Sign In"
4. **Expected:** Redirect to dashboard, see "Welcome back, testowner!" message

#### ✅ Test 2: Failed Login
1. Visit `http://127.0.0.1:8000/`
2. Enter wrong credentials (testowner / wrongpassword)
3. Click "Sign In"
4. **Expected:** Stay on login page, see "Invalid username or password." error message

#### ✅ Test 3: Already Logged In
1. Login successfully
2. Visit `http://127.0.0.1:8000/` again
3. **Expected:** Automatically redirect to dashboard

#### ✅ Test 4: Protected Route
1. Logout
2. Try to visit `http://127.0.0.1:8000/dashboard/`
3. **Expected:** Redirect to login page

#### ✅ Test 5: Logout
1. Login successfully
2. Click "Logout" button
3. **Expected:** Redirect to login page, see "You have been logged out successfully." message

#### ✅ Test 6: Role Display
1. Login as testowner
2. **Expected:** Dashboard shows "Role: OWNER"
3. Logout and login as admin1
4. **Expected:** Dashboard shows "Role: ADMINISTRATOR"

---

## 📊 Change Log

### Phase 1: Login & Authentication System (September 2026)

#### Files Created (14 new files)

| File | Purpose | Lines of Code |
|---|---|---|
| `ops/__init__.py` | Makes ops a Python package | 0 |
| `ops/apps.py` | App configuration | 5 |
| `ops/admin.py` | Django admin (empty) | 2 |
| `ops/models.py` | Models (empty) | 2 |
| `ops/tests.py` | Tests (empty) | 2 |
| `ops/views.py` | Login, logout, dashboard views | 65 |
| `ops/urls.py` | URL routes | 12 |
| `ops/migrations/__init__.py` | Migrations folder | 0 |
| `ops/templates/base.html` | Base template (shared layout) | 75 |
| `ops/templates/ops/login.html` | Login page | 95 |
| `ops/templates/ops/dashboard.html` | Dashboard page | 110 |
| `ops/static/css/app.css` | Custom CSS | 30 |
| `requirements_py311.txt` | Python 3.11 compatible requirements | 45 |
| `.env` | Environment variables | 10 |

**Total New Code:** ~438 lines

#### Files Modified (2 files)

| File | Changes | Lines Added |
|---|---|---|
| `core/settings.py` | Added ops app, templates, static, auth settings | +25 |
| `core/urls.py` | Added web frontend URLs | +10 |

**Total Modified Code:** ~35 lines

#### Features Implemented

- ✅ Login page with session-based authentication
- ✅ Dashboard with stats cards
- ✅ Logout functionality
- ✅ `@login_required` protection
- ✅ CSRF protection on forms
- ✅ Success/error messages
- ✅ Role-based user display
- ✅ Tailwind CSS with brand colors
- ✅ Material Symbols icons
- ✅ Pretendard font
- ✅ Responsive design

#### Technical Decisions

1. **Session Auth vs JWT**: Chose session-based auth for web (simpler, more secure)
2. **Hybrid Approach**: Kept existing API + added template layer
3. **Tailwind CDN**: Used Play CDN for development (fast iteration)
4. **Mock Data**: Used hardcoded stats for dashboard (will connect to real data later)

---

## 📚 References

### Design Documents

- **design.md**: Frontend design specifications (Material 3, Tailwind, colors)
- **techstack.md**: Technology stack decisions (Django, sessions, templates)
- **PRD.md**: Product requirements (features, user roles, scope)

### Architecture

- **Hybrid Approach (Option C)**: Keep API + add templates
- **Single App Structure**: `ops` app for all web views
- **Shared Database**: Both apps use same SQLite database
- **AUTH_USER_MODEL**: `authuser.User` for both API and web

### URLs

| URL | Purpose | Auth Required |
|---|---|---|
| `/` | Login page | No |
| `/dashboard/` | Dashboard | Yes |
| `/logout/` | Logout | Yes |
| `/api/v1/user/login/` | API login | No |
| `/api/v1/user/user-info/` | API user info | Yes (JWT) |
| `/admin/` | Django admin | Yes |
| `/api/swagger/` | API documentation | No |

---

## 🚀 Next Phases

### Phase 2: Client Management (Planned)
- [ ] Client list page (`/clients/`)
- [ ] Create client form
- [ ] Edit client form
- [ ] Delete client confirmation
- [ ] Connect to `client.Client` model

### Phase 3: Site Management (Planned)
- [ ] Site list page (`/sites/`)
- [ ] Create site form
- [ ] Edit site form
- [ ] Connect to `client.Site` model

### Phase 4: Schedule Management (Planned)
- [ ] Schedule list page (`/schedules/`)
- [ ] Create schedule form
- [ ] Calendar view
- [ ] Schedule filtering

### Phase 5: Invoice Management (Planned)
- [ ] Invoice list page (`/invoices/`)
- [ ] Invoice builder (line items, tax, totals)
- [ ] Invoice verification
- [ ] PDF export

### Phase 6: Reports (Planned)
- [ ] Profitability report
- [ ] Charts and graphs
- [ ] Export functionality

### Phase 7: Polish (Planned)
- [ ] Dark mode toggle
- [ ] Search functionality
- [ ] Notifications
- [ ] User profile page
- [ ] Tests for all views

---

## 🤝 Team Collaboration

### For Backend Developers

**What You Need to Know:**
- The `ops` app is for web templates only
- Don't modify `authuser` or `client` apps (they're for API)
- Both apps share the same database
- Use `authuser.User` model for all user operations

**How to Add New Web Pages:**
1. Create view in `ops/views.py`
2. Create template in `ops/templates/ops/`
3. Add URL route in `ops/urls.py`
4. Test with `python manage.py runserver`

### For Frontend Designers

**What You Can Edit:**
- `ops/templates/ops/login.html` - Login page design
- `ops/templates/ops/dashboard.html` - Dashboard design
- `ops/templates/base.html` - Base layout
- `ops/static/css/app.css` - Custom styles

**What NOT to Change:**
- Don't remove `{% csrf_token %}` from forms
- Don't change `name="username"` or `name="password"` on inputs
- Don't change `method="post"` or `action="{% url 'ops:login' %}"`
- Don't remove `{% extends 'base.html' %}`

### For DevOps

**Deployment Checklist:**
- [ ] Set `DEBUG=False` in `.env`
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Switch to PostgreSQL (update `DB_ENGINE` and `DB_NAME`)
- [ ] Run `python manage.py collectstatic`
- [ ] Use Gunicorn instead of `runserver`
- [ ] Set up WhiteNoise for static files
- [ ] Configure `ALLOWED_HOSTS`

---

##  Troubleshooting

### "ModuleNotFoundError: No module named 'decouple'"
**Fix:** Run `pip install -r requirements.txt` in activated virtual environment

### "Template does not exist"
**Fix:** Check `TEMPLATES` setting in `core/settings.py` has `'DIRS': [BASE_DIR / 'ops' / 'templates']`

### "Reverse for 'dashboard' not found"
**Fix:** Check `app_name = 'ops'` in `ops/urls.py` and use `{% url 'ops:dashboard' %}`

### "User not logging in"
**Fix:** 
- Check username/password in database
- Check `AUTH_USER_MODEL = 'authuser.User'` in settings
- Check browser console for errors

### "Static files not loading"
**Fix:**
- Check `STATICFILES_DIRS` in settings
- Check `{% load static %}` at top of template
- Check internet connection (Tailwind CDN)

### "CSS not showing (bare HTML)"
**Fix:**
- Don't use VS Code Live Preview
- Use `python manage.py runserver` and open `http://127.0.0.1:8000/`
- Check internet connection (Tailwind needs CDN)

---

## 📝 Quick Reference

### Common Django Commands

```bash
# Run server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Open Python shell
python manage.py shell

# Create superuser
python manage.py createsuperuser

# Collect static files (for production)
python manage.py collectstatic

# Run tests
python manage.py test

# Show migrations
python manage.py showmigrations
```

### Common Template Tags

```html
{% url 'ops:login' %}           <!-- Generate URL -->
{% static 'css/app.css' %}      <!-- Static file URL -->
{% if user.is_authenticated %}  <!-- Check if logged in -->
{% for item in items %}         <!-- Loop -->
{% extends 'base.html' %}       <!-- Inherit template -->
{% block content %}             <!-- Define block -->
{% csrf_token %}                <!-- CSRF token -->
{{ user.username }}             <!-- Display variable -->
{{ stats.active_jobs }}         <!-- Display number -->
```

### Common View Patterns

```python
# Render template
return render(request, 'ops/page.html', context)

# Redirect
return redirect('ops:dashboard')

# Get form data
username = request.POST.get('username')

# Check if logged in
if request.user.is_authenticated:

# Add message
messages.success(request, 'Success!')
messages.error(request, 'Error!')

# Protected view
@login_required
def my_view(request):
    ...
```

---

##  Learning Resources

### Django
- Official Docs: https://docs.djangoproject.com/
- Django Tutorial: https://docs.djangoproject.com/en/stable/intro/tutorial01/
- Django Templates: https://docs.djangoproject.com/en/stable/ref/templates/

### Tailwind CSS
- Docs: https://tailwindcss.com/docs
- Play CDN: https://tailwindcss.com/docs/installation/play-cdn

### Material Symbols
- Icons: https://fonts.google.com/icons
- Usage: https://developers.google.com/fonts/docs/material_symbols

### Project Docs
- design.md: Frontend design specifications
- techstack.md: Technology stack decisions
- PRD.md: Product requirements

---

## 📞 Support

For questions or issues:
1. Check this README first
2. Check Django documentation
3. Ask in team chat
4. Create an issue on GitHub

---

##  License

This project is part of the SubSync cleaning management platform.

---

**Last Updated:** September 3, 2026  
**Phase:** Login & Authentication System ✅ Complete  
**Next Phase:** Client Management (In Progress)
