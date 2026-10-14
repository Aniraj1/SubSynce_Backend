# SubSync

SubSync is a web app for a commercial cleaning business. It connects the people who run the business with the subcontractors who do the cleaning, and keeps the money side honest: what was scheduled, what was actually done, what the contractor billed, what the client paid, and what profit is left.

It is a Django project with two layers that share one database:

- **Web app (`ops`)**: server-rendered Django templates with Tailwind CSS and session login. This is what Owners, Administrators and Contractors use in the browser.
- **REST API** (`authuser`, `client`, `schedule`, `work`, `invoice`, `dashboard`): Django REST Framework with JWT, for mobile and other clients. Docs are served at `/api/swagger/` and `/api/redoc/`.

Three roles use the web app:

| Role | What they do |
|---|---|
| **Owner** | Everything an Administrator can do, plus Company Settings (business details and logo). |
| **Administrator** | Manages clients, sites, subcontractors, schedules and users; checks and approves contractor invoices; bills clients; reads the profitability report. |
| **Contractor** | Sees their assigned sites and services, submits invoices for completed work and tracks earnings. |

---

## My role (Aayush Rauniyar)

I led the **finance side of the web frontend** and acted as the integrator for the team: I proposed and built the invoicing, verification and reporting screens, merged the frontend and backend branches into one working app, and ran QA before each merge.

The team:

- **Aayush Rauniyar**: finance features, integration, QA, and the detail-page and dashboard rework listed below.
- **Roshani Ranjitkar**: frontend for user management, schedules, the contractor portal, the dashboard layout, the account menu, site images and the Subcontractors page.
- **Aniraj Khadgi**: the REST API and data models (users, clients, sites, schedules, work completion, invoices, dashboard and profit APIs), the `gst` invoice field, and the API test suites.

Parts of my work were built with AI-assisted pair programming (Claude Code); those commits show "Claude" as the author and were reviewed, tested and merged through my pull requests.

---

## Finance features I built

### Contractor invoices (`/invoices/`)

- **Invoice builder**: contractors pick a site and service period and add line items (description, quantity, unit price). The total updates live as they type, and the saved amount always equals the sum of the lines. Numbers are generated as `INV-YYYY-###`.
- **Verification against real work**: before an Administrator approves or rejects, the invoice page shows the evidence and raises flags when:
  - no completed work was recorded for that site and period,
  - fewer visits were recorded than were scheduled,
  - another contractor recorded work at the site in the same period,
  - the billed quantity is more than the recorded visits,
  - another invoice from the same contractor overlaps the same period.
- **Approve or reject** with notes; the reviewer and time are recorded.
- **A4 print view** that saves cleanly as a PDF.
- **Filters**: search by invoice number, site or contractor, filter by status, and filter by a **From/To invoice date range**.

### Client invoices (`/client-invoices/`, Administrator and Owner)

- A separate billing section for invoices sent to clients, numbered `CINV-YYYY-###`. The client is taken from the site, and the site's price is suggested as the unit price.
- Status flow: **Issued → Paid / Overdue / Cancelled**, and **Overdue → Paid / Cancelled**. Only paid invoices count as revenue.
- The detail page compares the invoice with the completed jobs in that period at the site's price, so under- or over-billing is visible before sending.
- Edit or delete while still Issued, plus an A4 print view.

### GST

- An **Include GST (10%)** tick box on both invoice builders, unticked by default.
- The stored amount stays ex-GST so reports compare like with like. GST is calculated at 10%, rounded to the cent, and shown as **Subtotal, GST and Total** in the builder, on the invoice page and on the PDF, which is titled **TAX INVOICE** when GST applies.
- Invoice lists mark GST invoices with "+ GST".

### Profitability report (`/reports/profitability/`)

- Profit per site, or rolled up per client: **revenue** (paid client invoices) minus **cost** (approved contractor invoices), with margin, a work-value column (completed jobs × site price) and totals.
- Optional date range and **CSV export**.
- **Losses are shown in red** across the report and the dashboard's This Month card, with the profit bar coloured by sign.

### Company settings and logo (`/settings/company/`, Owner only)

- Business name, ABN, phone, email, address and default payment terms, all printed on invoices.
- **Logo upload** (JPG, PNG or WebP, up to 2MB) with replace and remove. The uploaded logo appears on the invoice builders and printed invoices, falling back to the SubSync logo when none is set.

### Contractor earnings (My Invoices)

- The old separate Earnings page was folded into **My Invoices**: Pending, **Approved total** (with the number of approved invoices) and Rejected cards, plus a **12-month earnings** card.
- The earnings card is a small line graph of approved earnings per month with a value scale. Each month's segment is **green when earnings rose and red when they fell**, and the header shows this month against last month in the same colours. It is drawn with inline SVG, with no chart library.

---

## Other frontend work I built

- **Detail pages**: clicking a name now opens a full page instead of a pop-up:
  - **Site**: client, address, frequency, price, contractor, next scheduled service, cleaning instructions and a photo gallery, with Edit and Delete.
  - **Client**: contact details and their sites; each site name links to its page.
  - **Subcontractor**: profile, totals (sites, jobs completed, invoices, approved earnings), assigned sites, upcoming services and recent work.
  - **Schedule**: date, time, site, client, subcontractor, notes and instructions, plus the work record (check-in, check-out, time on site, notes and photos).
- **Tables tidied**: Sites shows Site, Frequency, Contractor and Actions; the separate View buttons were removed from Clients and Subcontractors.
- **Dashboards**: removed the placeholder Alerts & Notifications boxes from the admin and contractor dashboards; contractor clock-in and clock-out were removed from the web portal (the mobile API endpoints are unchanged).
- **Login**: the field is labelled "Email or Username", and both are accepted.
- **Design QA fixes**: removed the flash of icon names while the icon font loads, and fixed leftovers from merges (a duplicated Add Client header and a template comment that showed on the page).

---

## How I did QA

1. **Automated tests.** Every feature above has tests in `ops/tests/`. The web app suite has **104 tests**, covering invoice building and totals, GST, verification flags, client invoice status rules, the profitability maths, the company logo, role access, the detail pages, the earnings graph and the date filter. The backend API suite (Aniraj's) has **157 tests**. Both suites pass.
2. **Role-based manual checks.** Before each merge I logged in as Owner, Administrator and Contractor and opened every page, checking that each role sees only what it should (for example, contractors are blocked from staff pages, and only the Owner can open Company Settings). I also ran a script that loads every page for each role and reports any server error.
3. **Merge checks.** After each pull I reviewed what came in by author, ran `makemigrations --check` to catch missing or clashing migrations, ran both test suites, and compared screens against earlier work so nothing was silently undone.
4. **Light and dark mode.** Pages use the SubSync colour tokens, so I checked each new screen in both themes.
5. **Mobile.** Tables scroll sideways on small screens, card rows wrap (four cards become two per row), and I checked new pages at phone width.
6. **Design QA pass.** I checked fonts, spacing, money formatting (`$1,234.56`, tabular figures), loss colouring and empty states ("No photos yet", "Nothing scheduled") against the designs.

---

## Running the project

### Requirements

- Python 3.12 or newer (developed on 3.14)
- Git

### 1. Get the code and create a virtual environment

**Windows (PowerShell)**

```powershell
git clone https://github.com/aayushRauniyar/SubSynce_Backend_Frontend.git
cd SubSynce_Backend_Frontend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
git clone https://github.com/aayushRauniyar/SubSynce_Backend_Frontend.git
cd SubSynce_Backend_Frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create `.env`

Copy `sample.env` to `.env` in the project root and fill it in:

| Key | Example | Notes |
|---|---|---|
| `DEBUG` | `True` | Use `False` outside development. |
| `SECRET_KEY` | any long random string | Required. |
| `JWT_KEY` | any long random string | Required; signs API tokens. |
| `JWT_ACCESS_TOKEN_LIFETIME_HRS` | `4` | Must be more than 0, or API tokens expire immediately. |
| `JWT_REFRESH_TOKEN_LIFETIME_HRS` | `48` | |
| `PASSWORD_MIN_LENGTH` | `8` | Passwords also need upper case, lower case, a number and a special character. |
| `THROTTLE_RATES_IN_DAYS` | `1000000` | API request limit per day. |
| `SUPER_ADMIN_PASSWORD` | a strong password | Used by the API tests. |
| `DEFAULT_USER_PASSWORD` | the same value | Used by the API test factories; set it equal to `SUPER_ADMIN_PASSWORD`. |
| `DB_ENGINE`, `DB_NAME` | leave blank | Blank means SQLite in `db.sqlite3`. |

Password reset emails print to the terminal while `DEBUG=True`. For real email, set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` and the `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` and `DEFAULT_FROM_EMAIL` keys.

### 3. Set up the database and an Owner account

```bash
python manage.py migrate
python manage.py createsuperuser
```

`createsuperuser` makes an **Owner**. Add Administrators and Contractors from the Users page once you're logged in.

### 4. Run it

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in with your email or username. Django admin is at `/admin/`, and API docs are at `/api/swagger/`.

### Sharing a local run with ngrok (optional)

```bash
ngrok http 8000
```

`ALLOWED_HOSTS` already accepts any host, but Django rejects form posts (including the login form) from an untrusted HTTPS origin. Add this to `core/settings.py` before logging in through the ngrok address:

```python
CSRF_TRUSTED_ORIGINS = ["https://*.ngrok-free.app", "https://*.ngrok-free.dev"]
```

---

## Running the tests

**Web app (`ops`)**, using Django's test runner:

```bash
python manage.py test ops
```

**Backend API apps**, using pytest:

```bash
pytest --ignore=ops
```

The API tests read three values from `.env`: `DEFAULT_USER_PASSWORD` and `SUPER_ADMIN_PASSWORD` must be set to the same value, and `JWT_ACCESS_TOKEN_LIFETIME_HRS` must be more than 0. With a value of 0, every authenticated test fails with 401.

Check for missing migrations with:

```bash
python manage.py makemigrations --check --dry-run
```

---

## Project layout

```
core/         settings and URL routing (web app at /, API at /api/)
ops/          the web app: views, templates, static files, services and tests
  services.py     shared money logic (totals, GST, verification, profitability, earnings)
  views_invoices.py, views_client_invoices.py, views_reports.py, views_settings.py
  templates/ops/  pages; partials/ holds shared pieces such as the sidebar and stat cards
  tests/          web app tests
authuser/     users, roles and login API
client/       clients, sites and site images
schedule/     service schedules
work/         work completion records and photos
invoice/      contractor and client invoices (including the gst field)
dashboard/    dashboard and profit APIs
```
