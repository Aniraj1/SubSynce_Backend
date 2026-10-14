import csv
import uuid
from datetime import timedelta
from decimal import Decimal

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Min, Prefetch, Q, Sum
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST, require_http_methods

from client.model.clientmanage import Client, Site, SiteImage
from authuser.model.user import User
from schedule.model.cleaningschedule import ServiceSchedule
from work.model.workcomplete import CompleteWork
from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from ops import services
from ops.access import STAFF_ROLES, contractor_required, forbidden, is_contractor, is_staff_user
from ops.forms import MANAGEABLE_ROLES, clean_evidence_photos, ClientCreateForm, ClientForm, ScheduleForm, ScheduleStatusForm, SiteForm, SubcontractorForm, UserForm


def _contractor_label(user):
    """Short display name for a contractor: 'First L.' if available, else username."""
    if not user:
        return None
    detail = getattr(user, 'user_detail', None)
    if detail and detail.first_name:
        last_initial = f" {detail.last_name[0]}." if detail.last_name else ""
        return f"{detail.first_name}{last_initial}"
    return user.username


def _full_name(user):
    """'First Last' if a UserDetail exists, else the username."""
    detail = getattr(user, 'user_detail', None)
    if detail and detail.first_name:
        return f"{detail.first_name} {detail.last_name or ''}".strip()
    return user.username


def _build_contractor_portal_context(request):
    """
    Context for the Contractor Portal - mirrors the filtering rules already
    enforced server-side in schedule/work/invoice's user_views.py (same
    site__assigned_contractor / completed_by / created_by scoping), just
    computed directly via the ORM for this session-authenticated page instead
    of calling those JWT-authenticated DRF endpoints.
    """
    user = request.user
    today = timezone.localdate()
    my_schedules = ServiceSchedule.objects.filter(site__assigned_contractor=user)

    assigned = (
        my_schedules.filter(status='SCHEDULED', scheduled_date__gte=today)
        .select_related('site')
        .order_by('scheduled_date', 'scheduled_time')[:6]
    )
    assigned_jobs = []
    for schedule in assigned:
        work = getattr(schedule, 'work_completion', None)
        badge = work.status.replace('_', ' ').title() if work else schedule.status.title()
        assigned_jobs.append({
            'time': schedule.scheduled_time,
            'date': schedule.scheduled_date,
            'is_today': schedule.scheduled_date == today,
            'id': schedule.id,
            'site_name': schedule.site.name,
            'site_address': schedule.site.address,
            'service_info': schedule.site.cleaning_frequency,
            'status': badge,
        })

    return {
        'dashboard': services.contractor_dashboard(user),  # summary cards: same figures as the ContractorDashboard API
        'assigned_jobs': assigned_jobs,
    }


def login_view(request):
    """
    Login view - handles user authentication with Django sessions
    
    GET: Shows the login form
    POST: Processes the login form
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('ops:dashboard')
    
    # Handle POST request (form submission)
    identifier = ''
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        # The field asks for an email, but usernames still work (not every user has an email).
        # An email only resolves when exactly one user has it, since emails aren't unique.
        username = identifier
        if '@' in identifier:
            matches = list(User.objects.filter(email__iexact=identifier).values_list('username', flat=True)[:2])
            if len(matches) == 1:
                username = matches[0]

        # Authenticate user against the database
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Login successful - create session
            login(request, user)
            # Unticked "Remember Me" ends the session when the browser closes;
            # ticked keeps the default SESSION_COOKIE_AGE.
            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)
            messages.success(request, f'Welcome back, {user.username}!')

            # Redirect to dashboard (or next page if specified)
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect('ops:dashboard')
        else:
            # Login failed
            messages.error(request, 'Invalid email/username or password.')

    # Handle GET request (show login form)
    return render(request, 'ops/login.html', {'identifier': identifier})


def logout_view(request):
    """
    Logout view - ends user session and redirects to login
    
    This view logs out the user, clears the session, and redirects to login page
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('ops:login')


@login_required
def dashboard_view(request):
    """
    Dashboard view - shows overview of the system.

    Branches by role: CONTRACTOR users get the Contractor Portal; staff
    (ADMINISTRATOR, OWNER) get the admin dashboard; anyone else gets a 403.
    Staff figures come from the ORM (same patterns as the dashboard API), plus
    the shared services.admin_summary, which ?start=YYYY-MM-DD&end=YYYY-MM-DD narrows.
    """
    user = request.user

    if is_contractor(user):
        context = {
            'user': user,
            'full_name': _full_name(user),
            **_build_contractor_portal_context(request),
        }
        return render(request, 'ops/subcontractor_portal.html', context)
    if not is_staff_user(user):
        return forbidden(request)

    start = services.parse_date(request.GET.get('start'))
    end = services.parse_date(request.GET.get('end'))
    range_error = None
    if start and end and start > end:
        range_error = 'Start date must be on or before the end date.'
        start = end = None

    today = timezone.localdate()

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    week_schedules = ServiceSchedule.objects.filter(
        scheduled_date__range=[week_start, week_end]
    )
    jobs_scheduled = week_schedules.count()
    jobs_completed = CompleteWork.objects.filter(
        status='COMPLETED',
        schedule__scheduled_date__range=[week_start, week_end],
    ).count()
    jobs_progress_pct = (
        round(jobs_completed / jobs_scheduled * 100) if jobs_scheduled else 0
    )

    upcoming = (
        ServiceSchedule.objects.filter(status='SCHEDULED', scheduled_date__gte=today)
        .select_related('site', 'site__client_id', 'site__assigned_contractor', 'site__assigned_contractor__user_detail')
        .order_by('scheduled_date', 'scheduled_time')[:6]
    )
    upcoming_services = [
        {
            'site_name': schedule.site.name,
            'client_name': f"{schedule.site.client_id.first_name} {schedule.site.client_id.last_name or ''}".strip(),
            'date': schedule.scheduled_date,
            'time': schedule.scheduled_time,
            'contractor': _contractor_label(schedule.site.assigned_contractor),
            'status': schedule.status,
        }
        for schedule in upcoming
    ]

    contractor_invoices_pending = ContractorInvoice.objects.filter(status='PENDING').count()
    recent_invoice = (
        ClientInvoice.objects.select_related('site')
        .order_by('-invoice_date', '-created_at')
        .first()
    )

    month_revenue = ClientInvoice.objects.filter(
        status='PAID', invoice_date__year=today.year, invoice_date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_cost = ContractorInvoice.objects.filter(
        status='APPROVED', invoice_date__year=today.year, invoice_date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_profit = month_revenue - month_cost
    month_margin = round(month_profit / month_revenue * 100, 1) if month_revenue else Decimal('0.0')

    context = {
        'user': user,
        'today': today,
        'stats': {
            'clients': Client.objects.count(),
            'sites': Site.objects.count(),
            'contractors': User.objects.filter(role='CONTRACTOR', deleted_at__isnull=True).count(),
        },
        'jobs_this_week': {
            'completed': jobs_completed,
            'scheduled': jobs_scheduled,
            'progress_pct': jobs_progress_pct,
        },
        'upcoming_services': upcoming_services,
        'invoices_summary': {
            'pending': contractor_invoices_pending,
            'flagged': 0,  # no "flagged" status exists on any invoice model yet
            'recent': recent_invoice,
        },
        'month_financials': {
            'revenue': month_revenue,
            'cost': month_cost,
            'profit': month_profit,
            'margin': month_margin,
            # Bar length: size of the margin, capped at 100%; the colour shows the sign.
            'margin_bar': min(abs(month_margin), 100),
        },
        'summary': services.admin_summary(start, end),
        'today_jobs': services.todays_schedule(),
        'pending_invoices': (
            ContractorInvoice.objects.filter(status='PENDING')
            .select_related('site', 'created_by')
            .order_by('invoice_date')[:5]
        ),
        'start': start,
        'end': end,
        'range_error': range_error,
    }

    return render(request, 'ops/dashboard.html', context)


def _is_admin(request):
    # The Owner is the superuser, so they get every administrator screen too.
    return request.user.is_authenticated and request.user.role in STAFF_ROLES


def _filtered_clients(request):
    """Clients matching ?q= (name/phone/email) and ?status= (a real Client status); shared by the list and its CSV export."""
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip().upper()
    if status not in dict(Client.STATUS_CHOICES):
        status = ''
    clients = Client.objects.all().prefetch_related('sites', 'assigned_sites').order_by('-created_at')
    if query:
        clients = clients.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
        )
    if status:
        clients = clients.filter(status=status)
    return clients, query, status


def _clients_csv(clients):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="clients_{timezone.localdate():%Y-%m-%d}.csv"'
    response.write('\ufeff')  # UTF-8 byte order mark so Excel reads non-ASCII names correctly
    writer = csv.writer(response)
    writer.writerow(['Client', 'Phone', 'Email', 'Assigned Sites', 'Status'])
    for c in clients:
        writer.writerow([f"{c.first_name} {c.last_name or ''}".strip(), c.phone or '', c.email or '',
                         c.sites.count(), c.get_status_display()])
    return response


@login_required
def clients_view(request):
    """
    Clients list page - Administrator only.

    Supports search (?q=) across name/phone/email, a status filter (?status=ACTIVE|INACTIVE),
    pagination (?page=), and ?format=csv to download the filtered list.
    """
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access client management.')
        return redirect('ops:dashboard')

    clients, query, status = _filtered_clients(request)
    if request.GET.get('format') == 'csv':
        return _clients_csv(clients)

    paginator = Paginator(clients, 8)
    page_obj = paginator.get_page(request.GET.get('page'))
    filters = {k: v for k, v in {'q': query, 'status': status}.items() if v}

    context = {
        'user': request.user,
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'status_choices': Client.STATUS_CHOICES,
        'filter_qs': urlencode(filters),
        'export_qs': urlencode({**filters, 'format': 'csv'}),
        'total_clients': paginator.count,
        'client_form': ClientForm(),  # site + status options for the Edit Client modal
    }
    return render(request, 'ops/clients.html', context)


@login_required
def subcontractors_view(request):
    """
    Contractors list page - Administrator only.

    Edit opens a modal (subcontractor_update_view); Delete reuses user_delete_view,
    which refuses while the contractor still has linked records.
    Supports search (?q=) across name/username/email/phone and pagination.
    """
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access contractor management.')
        return redirect('ops:dashboard')

    query = request.GET.get('q', '').strip()
    contractors = (
        User.objects.filter(role='CONTRACTOR', deleted_at__isnull=True)
        .select_related('user_detail')
        .annotate(site_count=Count('contractors', distinct=True))
        .order_by('username')
    )

    if query:
        contractors = contractors.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(user_detail__first_name__icontains=query)
            | Q(user_detail__last_name__icontains=query)
            | Q(user_detail__phone__icontains=query)
        )

    paginator = Paginator(contractors, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'user': request.user,
        'page_obj': page_obj,
        'query': query,
        'total_contractors': paginator.count,
        'edit_state': request.session.pop('subcontractor_form_state', None),  # set by a failed edit
        'add_state': request.session.pop('user_form_state', None),  # set by a failed Add Contractor (user_create)
    }
    return render(request, 'ops/subcontractors.html', context)


@login_required
def subcontractor_detail_view(request, pk):
    """One contractor's profile, sites, upcoming services, recent work and invoices - Administrator only."""
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access contractor management.')
        return redirect('ops:dashboard')

    contractor = get_object_or_404(
        User.objects.select_related('user_detail'), id=pk, role='CONTRACTOR', deleted_at__isnull=True
    )
    today = timezone.localdate()
    invoices = ContractorInvoice.objects.filter(created_by=contractor)
    context = {
        'user': request.user,
        'contractor': contractor,
        'full_name': _full_name(contractor),
        'phone': getattr(getattr(contractor, 'user_detail', None), 'phone', None),
        'sites': contractor.contractors.select_related('client_id').order_by('name'),
        'upcoming': ServiceSchedule.objects.filter(
            site__assigned_contractor=contractor, status='SCHEDULED', scheduled_date__gte=today
        ).select_related('site').order_by('scheduled_date', 'scheduled_time')[:10],
        'recent_work': contractor.work_completions.select_related('schedule__site')
            .order_by('-check_in_time')[:10],
        'completed_count': contractor.work_completions.filter(status='COMPLETED').count(),
        'invoice_counts': {
            'pending': invoices.filter(status='PENDING').count(),
            'approved': invoices.filter(status='APPROVED').count(),
            'rejected': invoices.filter(status='REJECTED').count(),
        },
        'approved_total': invoices.filter(status='APPROVED').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
    }
    return render(request, 'ops/subcontractor_detail.html', context)


@login_required
def client_detail_view(request, pk):
    """Client details page with the client's own sites - Administrator only."""
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access client management.')
        return redirect('ops:dashboard')

    client = get_object_or_404(Client, id=pk)
    context = {
        'user': request.user,
        'client': client,
        'sites': _with_images(client.sites.order_by('name')),
        'client_form': ClientForm(),  # site + status options for the Edit Client modal
        **_site_form_context(),
    }
    return render(request, 'ops/client_detail.html', context)


def _site_form_context():
    """Dropdown data for the shared Add/Edit Site modal."""
    return {
        'clients': Client.objects.order_by('first_name', 'last_name'),
        'frequencies': sorted(set(Site.objects.values_list('cleaning_frequency', flat=True)), key=str.lower),
        'contractors': User.objects.filter(role='CONTRACTOR', deleted_at__isnull=True).order_by('username'),
    }


def _redirect_back(request, default):
    """Redirect to a safe local `next` URL from the POST body, else `default`."""
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(default)


@login_required
@require_http_methods(['GET', 'POST'])
def client_create_view(request):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage clients.')
        return redirect('ops:dashboard')

    if request.method == 'GET':
        return render(request, 'ops/client_add.html', {'user': request.user, 'form': ClientCreateForm()})

    form = ClientCreateForm(request.POST, request.FILES)
    if form.is_valid():
        email = form.cleaned_data.get('email')
        if email and Client.objects.filter(email=email).exists():
            form.add_error('email', 'A client with this email already exists.')
            return render(request, 'ops/client_add.html', {'user': request.user, 'form': form})
        try:
            client = form.save()
        except IntegrityError:
            # Deleted clients are soft-deleted, so their phone number still
            # occupies the unique index even though the form can't see them.
            form.add_error('phone', 'This phone number belongs to a removed client. Use a different number.')
            return render(request, 'ops/client_add.html', {'user': request.user, 'form': form})
        messages.success(request, 'Client added successfully.')
        return redirect('ops:client_detail', pk=client.pk)

    messages.error(request, 'Could not add client. Please check the details and try again.')
    return render(request, 'ops/client_add.html', {'user': request.user, 'form': form})


@login_required
@require_POST
def client_update_view(request, pk):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage clients.')
        return redirect('ops:dashboard')

    client = Client.objects.filter(id=pk).first()
    if not client:
        messages.error(request, 'Client not found.')
        return redirect('ops:clients')

    form = ClientForm(request.POST, request.FILES, instance=client)
    if form.is_valid():
        phone = form.cleaned_data.get('phone')
        if phone and Client.objects.filter(phone=phone).exclude(id=pk).exists():
            messages.error(request, 'A client with this phone number already exists.')
            return _redirect_back(request, 'ops:clients')
        try:
            form.save()
        except IntegrityError:
            messages.error(request, 'This phone number belongs to a removed client. Use a different number.')
            return _redirect_back(request, 'ops:clients')
        messages.success(request, 'Client updated successfully.')
    else:
        messages.error(request, 'Could not update client. Please check the details and try again.')

    return _redirect_back(request, 'ops:clients')


@login_required
@require_POST
def client_delete_view(request, pk):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage clients.')
        return redirect('ops:dashboard')

    client = Client.objects.filter(id=pk).first()
    if client:
        client.delete()
        messages.success(request, 'Client removed successfully.')
    else:
        messages.error(request, 'Client not found.')

    return redirect('ops:clients')


@login_required
def sites_view(request):
    """
    Sites list page - Administrator only.

    Supports search (?q=) across site name/address/client name, filtering by
    client (?client=) and frequency (?frequency=), and pagination (?page=).
    """
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access site management.')
        return redirect('ops:dashboard')

    query = request.GET.get('q', '').strip()
    client_filter = request.GET.get('client', '').strip()
    frequency = request.GET.get('frequency', '').strip()

    sites = _with_images(
        Site.objects.select_related('client_id', 'assigned_contractor__user_detail').order_by('name')
    )
    if query:
        sites = sites.filter(
            Q(name__icontains=query)
            | Q(address__icontains=query)
            | Q(client_id__first_name__icontains=query)
            | Q(client_id__last_name__icontains=query)
        )
    try:
        if client_filter:
            sites = sites.filter(client_id=uuid.UUID(client_filter))
    except ValueError:
        client_filter = ''
    if frequency:
        sites = sites.filter(cleaning_frequency__iexact=frequency)

    paginator = Paginator(sites, 8)
    page_obj = paginator.get_page(request.GET.get('page'))
    for site in page_obj:
        site.contractor_name = _full_name(site.assigned_contractor) if site.assigned_contractor else None
    filters = {k: v for k, v in {'q': query, 'client': client_filter, 'frequency': frequency}.items() if v}

    context = {
        'user': request.user,
        'page_obj': page_obj,
        'total_sites': paginator.count,
        'query': query,
        'client_filter': client_filter,
        'frequency': frequency,
        'filter_qs': urlencode(filters),
        **_site_form_context(),
    }
    return render(request, 'ops/sites.html', context)


@login_required
def site_detail_view(request, pk):
    """One site's full details and photo gallery - Administrator only."""
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access site management.')
        return redirect('ops:dashboard')

    site = get_object_or_404(
        _with_images(Site.objects.select_related('client_id', 'assigned_contractor__user_detail')), id=pk
    )
    today = timezone.localdate()
    context = {
        'user': request.user,
        'site': site,
        'contractor_name': _full_name(site.assigned_contractor) if site.assigned_contractor else None,
        'next_service': site.service_schedules.filter(scheduled_date__gte=today, status='SCHEDULED')
            .order_by('scheduled_date', 'scheduled_time').first(),
        **_site_form_context(),
    }
    return render(request, 'ops/site_detail.html', context)


def _with_images(sites):
    """Prefetch each site's gallery (SiteImage, related_name='images'): only rows with a file, oldest first."""
    return sites.prefetch_related(Prefetch(
        'images', queryset=SiteImage.objects.exclude(image='').exclude(image__isnull=True).order_by('created_at')
    ))


def _save_site(request, instance=None):
    """
    Validate and save a SiteForm, flashing the outcome. Images follow the Site API:
    uploads are added as SiteImage rows (like `site_image` / POST site-image/), and
    ticked existing images are removed (like DELETE remove-site-image/); others are kept.
    """
    form = SiteForm(request.POST, instance=instance)
    images = request.FILES.getlist('images')
    try:
        clean_evidence_photos(images)  # real images, 5MB max each
    except ValidationError as e:
        messages.error(request, f"Could not save site. Images: {' '.join(e.messages)}")
        return _redirect_back(request, 'ops:sites')
    if form.is_valid():
        with transaction.atomic():
            site = form.save()
            for image in images:
                SiteImage.objects.create(site=site, image=image)
            if instance:
                remove_ids = [i for i in map(_uuid_or_none, request.POST.getlist('remove_images')) if i]
                for image in SiteImage.objects.filter(site=site, id__in=remove_ids):
                    image.delete()
        messages.success(request, 'Site updated successfully.' if instance else 'Site added successfully.')
    else:
        errors = '; '.join(f"{form.fields[f].label if f in form.fields else f}: {' '.join(e)}" for f, e in form.errors.items())
        messages.error(request, f'Could not save site. {errors}')
    return _redirect_back(request, 'ops:sites')


@login_required
@require_POST
def site_create_view(request):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage sites.')
        return redirect('ops:dashboard')
    return _save_site(request)


@login_required
@require_POST
def site_update_view(request, pk):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage sites.')
        return redirect('ops:dashboard')
    site = Site.objects.filter(id=pk).first()
    if not site:
        messages.error(request, 'Site not found.')
        return _redirect_back(request, 'ops:sites')
    return _save_site(request, instance=site)


@login_required
@require_POST
def site_delete_view(request, pk):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage sites.')
        return redirect('ops:dashboard')
    site = Site.objects.filter(id=pk).first()
    if site:
        site.delete()
        messages.success(request, 'Site removed successfully.')
    else:
        messages.error(request, 'Site not found.')
    return _redirect_back(request, 'ops:sites')


SCHEDULE_PERIODS = [('week', 'This Week'), ('next_week', 'Next Week'), ('month', 'This Month'), ('all', 'All Dates')]


@login_required
def schedules_view(request):
    """
    Schedules list page - Administrator only.

    Search (?q=) across site/client/contractor names, filters by site (?site=),
    status (?status=) and period (?period=, defaults to this week), pagination (?page=).
    """
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access schedules.')
        return redirect('ops:dashboard')

    query = request.GET.get('q', '').strip()
    site_filter = request.GET.get('site', '').strip()
    status = request.GET.get('status', '').strip()
    period = request.GET.get('period', 'week')
    if period not in dict(SCHEDULE_PERIODS):
        period = 'week'
    status_choices = ServiceSchedule._meta.get_field('status').choices

    schedules = ServiceSchedule.objects.select_related(
        'site__client_id', 'site__assigned_contractor__user_detail'
    ).order_by('scheduled_date', 'scheduled_time')
    if query:
        schedules = schedules.filter(
            Q(site__name__icontains=query)
            | Q(site__client_id__first_name__icontains=query)
            | Q(site__client_id__last_name__icontains=query)
            | Q(site__assigned_contractor__username__icontains=query)
            | Q(site__assigned_contractor__user_detail__first_name__icontains=query)
            | Q(site__assigned_contractor__user_detail__last_name__icontains=query)
        )
    try:
        if site_filter:
            schedules = schedules.filter(site_id=uuid.UUID(site_filter))
    except ValueError:
        site_filter = ''
    if status in dict(status_choices):
        schedules = schedules.filter(status=status)
    else:
        status = ''

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    if period == 'week':
        schedules = schedules.filter(scheduled_date__range=(week_start, week_start + timedelta(days=6)))
    elif period == 'next_week':
        schedules = schedules.filter(scheduled_date__range=(week_start + timedelta(days=7), week_start + timedelta(days=13)))
    elif period == 'month':
        schedules = schedules.filter(scheduled_date__year=today.year, scheduled_date__month=today.month)

    paginator = Paginator(schedules, 8)
    page_obj = paginator.get_page(request.GET.get('page'))
    for schedule in page_obj:
        contractor = schedule.site.assigned_contractor
        schedule.contractor_name = _full_name(contractor) if contractor else ''

    # Site options for the modal, with the client/contractor shown as read-only context.
    sites = list(ScheduleForm().fields['site'].queryset)
    for site in sites:
        site.contractor_name = _full_name(site.assigned_contractor) if site.assigned_contractor else ''

    filters = {k: v for k, v in {'q': query, 'site': site_filter, 'status': status, 'period': period}.items() if v}
    context = {
        'user': request.user,
        'page_obj': page_obj,
        'total_schedules': paginator.count,
        'query': query,
        'site_filter': site_filter,
        'status': status,
        'period': period,
        'periods': SCHEDULE_PERIODS,
        'status_choices': status_choices,
        'filter_qs': urlencode(filters),
        'sites': sites,
    }
    return render(request, 'ops/schedules.html', context)


@login_required
def schedule_detail_view(request, pk):
    """One scheduled service: site, client, contractor, timing, notes and its work record - Administrator only."""
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access schedules.')
        return redirect('ops:dashboard')

    schedule = get_object_or_404(
        ServiceSchedule.objects.select_related(
            'site__client_id', 'site__assigned_contractor__user_detail', 'created_by'
        ),
        id=pk,
    )
    contractor = schedule.site.assigned_contractor
    work = (
        CompleteWork.objects.filter(schedule=schedule)
        .select_related('completed_by').prefetch_related('work_completion_images').first()
    )
    context = {
        'user': request.user,
        's': schedule,
        'contractor': contractor,
        'contractor_name': _full_name(contractor) if contractor else None,
        'work': work,
        'duration': (work.check_out_time - work.check_in_time)
            if work and work.check_in_time and work.check_out_time else None,
    }
    return render(request, 'ops/schedule_detail.html', context)


def _save_schedule(request, instance=None):
    """Validate and save a ScheduleForm, flashing the outcome."""
    form = ScheduleForm(request.POST, instance=instance)
    if form.is_valid():
        schedule = form.save(commit=False)
        if not instance:
            schedule.created_by = request.user
        schedule.save()
        messages.success(request, 'Schedule updated successfully.' if instance else 'Schedule added successfully.')
    else:
        errors = '; '.join(f"{form.fields[f].label if f in form.fields else f}: {' '.join(e)}" for f, e in form.errors.items())
        messages.error(request, f'Could not save schedule. {errors}')
    return _redirect_back(request, 'ops:schedules')


@login_required
@require_POST
def schedule_create_view(request):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage schedules.')
        return redirect('ops:dashboard')
    return _save_schedule(request)


@login_required
@require_POST
def schedule_update_view(request, pk):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage schedules.')
        return redirect('ops:dashboard')
    schedule = ServiceSchedule.objects.filter(id=pk).first()
    if not schedule:
        messages.error(request, 'Schedule not found.')
    elif schedule.status != 'SCHEDULED':
        messages.error(request, 'Only scheduled services can be edited.')
    else:
        return _save_schedule(request, instance=schedule)
    return _redirect_back(request, 'ops:schedules')


@login_required
@require_POST
def schedule_status_view(request, pk):
    """Change a schedule's status; like the API, only SCHEDULED services can change."""
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage schedules.')
        return redirect('ops:dashboard')
    schedule = ServiceSchedule.objects.filter(id=pk).first()
    if not schedule:
        messages.error(request, 'Schedule not found.')
    elif schedule.status != 'SCHEDULED':
        messages.error(request, 'Only scheduled services can change status.')
    else:
        form = ScheduleStatusForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule status updated.')
        else:
            messages.error(request, 'Could not update status. Please choose a valid status.')
    return _redirect_back(request, 'ops:schedules')


@login_required
@require_POST
def schedule_delete_view(request, pk):
    """Cancels the schedule, matching the admin Schedule API's DELETE (the record is kept)."""
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage schedules.')
        return redirect('ops:dashboard')
    schedule = ServiceSchedule.objects.filter(id=pk).first()
    if not schedule:
        messages.error(request, 'Schedule not found.')
    elif schedule.status == 'CANCELLED':
        messages.error(request, 'Schedule is already cancelled.')
    else:
        schedule.status = 'CANCELLED'
        schedule.save()
        messages.success(request, 'Schedule cancelled.')
    return _redirect_back(request, 'ops:schedules')


def _can_manage(actor, target):
    """Same role rules as the register APIs; nobody edits/deletes their own account here."""
    return target.pk != actor.pk and target.role in MANAGEABLE_ROLES.get(actor.role, ())


def _linked_records(user):
    """Business records a soft delete would cascade into (assigned sites, schedules, invoices, work)."""
    return [
        str(rel.related_model._meta.verbose_name_plural)
        for rel in User._meta.related_objects
        if rel.one_to_many and rel.related_model.__name__ not in ('LogEntry', 'OutstandingToken')
        and getattr(user, rel.get_accessor_name()).exists()
    ]


@login_required
def users_view(request):
    """User Management - Administrators (manage contractors) and Owners (manage admins + contractors)."""
    if request.user.role not in MANAGEABLE_ROLES:
        messages.error(request, 'Only administrators can manage users.')
        return redirect('ops:dashboard')

    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    role_choices = User._meta.get_field('role').choices

    users = User.objects.filter(deleted_at__isnull=True).select_related('user_detail').order_by('username')
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(user_detail__first_name__icontains=query)
            | Q(user_detail__last_name__icontains=query)
        )
    if role in dict(role_choices):
        users = users.filter(role=role)
    else:
        role = ''

    paginator = Paginator(users, 8)
    page_obj = paginator.get_page(request.GET.get('page'))
    for u in page_obj:
        u.display_name = _full_name(u)
        u.initials = ''.join(part[0] for part in u.display_name.split()[:2]).upper()
        if not u.last_login:
            u.last_active = 'Never'
        elif timezone.now() - u.last_login < timedelta(minutes=1):
            u.last_active = 'Just now'
        else:
            u.last_active = f"{timesince(u.last_login, depth=1)} ago"
        u.can_manage = _can_manage(request.user, u)
        u.detail = getattr(u, 'user_detail', None)

    filters = {k: v for k, v in {'q': query, 'role': role}.items() if v}
    context = {
        'user': request.user,
        'page_obj': page_obj,
        'total_users': paginator.count,
        'query': query,
        'role': role,
        'role_choices': role_choices,
        'filter_qs': urlencode(filters),
        'form': UserForm(actor=request.user),
        'user_form_state': request.session.pop('user_form_state', None),  # set by a failed add/edit
    }
    return render(request, 'ops/users.html', context)


def _form_errors(form):
    """Field -> messages, for re-showing a modal's errors after a redirect."""
    return {
        ('non_field' if f == '__all__' else f): [e['message'] for e in errs]
        for f, errs in form.errors.get_json_data().items()
    }


def _save_user(request, instance=None):
    form = UserForm(request.POST, instance=instance, actor=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'User updated successfully.' if instance else 'User added successfully.')
    else:
        # Reopen the modal after the redirect with what was typed (never passwords) and the field errors.
        request.session['user_form_state'] = {
            'modal': {
                'action': '' if form.creating else request.path,
                'firstName': request.POST.get('first_name', ''),
                'lastName': request.POST.get('last_name', ''),
                'username': request.POST.get('username', ''),
                'email': request.POST.get('email', ''),
                'role': request.POST.get('role', ''),
            },
            'errors': _form_errors(form),
        }
        messages.error(request, 'Could not save user. Please fix the errors shown in the form.')
    return _redirect_back(request, 'ops:users')


def _managed_user_or_none(request, pk):
    """The target user if the current user may manage them, else None (with an error message)."""
    target = User.objects.filter(id=pk, deleted_at__isnull=True).first()
    if not target:
        messages.error(request, 'User not found.')
    elif not _can_manage(request.user, target):
        messages.error(request, "You don't have permission to manage this user.")
    else:
        return target
    return None


@login_required
@require_POST
def user_create_view(request):
    if request.user.role not in MANAGEABLE_ROLES:
        messages.error(request, 'Only administrators can manage users.')
        return redirect('ops:dashboard')
    return _save_user(request)


@login_required
@require_POST
def user_update_view(request, pk):
    if request.user.role not in MANAGEABLE_ROLES:
        messages.error(request, 'Only administrators can manage users.')
        return redirect('ops:dashboard')
    target = _managed_user_or_none(request, pk)
    return _save_user(request, instance=target) if target else _redirect_back(request, 'ops:users')


@login_required
@require_POST
def subcontractor_update_view(request, pk):
    """Edit a contractor's name, username, email and phone from the Contractors page."""
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage contractors.')
        return redirect('ops:dashboard')
    target = _managed_user_or_none(request, pk)
    if target and target.role != 'CONTRACTOR':
        messages.error(request, 'Only contractor accounts can be edited here.')
    elif target:
        form = SubcontractorForm(request.POST, instance=target, actor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contractor updated successfully.')
        else:
            request.session['subcontractor_form_state'] = {
                'modal': {
                    'action': request.path,
                    **{k: request.POST.get(k, '') for k in ('first_name', 'last_name', 'username', 'email', 'phone')},
                },
                'errors': _form_errors(form),
            }
            messages.error(request, 'Could not update contractor. Please fix the errors shown in the form.')
    return _redirect_back(request, 'ops:subcontractors')


@login_required
@require_POST
def user_delete_view(request, pk):
    """
    Soft delete (project convention) and disable login. Refused while the user still
    has linked records, because the soft delete would cascade into them.
    """
    if request.user.role not in MANAGEABLE_ROLES:
        messages.error(request, 'Only administrators can manage users.')
        return redirect('ops:dashboard')
    target = _managed_user_or_none(request, pk)
    if target:
        linked = _linked_records(target)
        if linked:
            messages.error(request, f"Can't delete {target.username}: they still have linked {', '.join(linked)}. Reassign or remove those first.")
        else:
            target.set_unusable_password()  # soft-deleted users would otherwise still be able to log in
            target.save()
            target.delete()
            messages.success(request, 'User removed successfully.')
    return _redirect_back(request, 'ops:users')


def _uuid_or_none(value):
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None


@contractor_required
def my_sites_view(request):
    """Read-only list of the contractor's own assigned sites (ContractorDashboard `sites`)."""
    upcoming = Q(
        service_schedules__status='SCHEDULED',
        service_schedules__scheduled_date__gte=timezone.localdate(),
        service_schedules__deleted_at__isnull=True,
    )
    sites = _with_images(
        Site.objects.filter(assigned_contractor=request.user).order_by('name').annotate(
            upcoming_count=Count('service_schedules', filter=upcoming),
            next_service=Min('service_schedules__scheduled_date', filter=upcoming),
        )
    )
    return render(request, 'ops/contractor/my_sites.html', {'sites': sites})


@contractor_required
def my_site_detail_view(request, pk):
    """One of the contractor's own sites: details, photos, upcoming services and their past work there.

    Sites assigned to someone else 404, so contractors can't read other contractors' sites.
    The site price (what the client is charged) is left out on purpose.
    """
    site = get_object_or_404(
        _with_images(Site.objects.select_related('client_id')), id=pk, assigned_contractor=request.user
    )
    today = timezone.localdate()
    context = {
        'site': site,
        'upcoming': site.service_schedules.filter(status='SCHEDULED', scheduled_date__gte=today)
            .order_by('scheduled_date', 'scheduled_time')[:10],
        'my_work': CompleteWork.objects.filter(schedule__site=site, completed_by=request.user)
            .select_related('schedule').order_by('-check_in_time')[:10],
    }
    return render(request, 'ops/contractor/site_detail.html', context)


@contractor_required
def my_job_detail_view(request, pk):
    """One scheduled service on the contractor's own site: when, where, what to do, and their work record."""
    job = get_object_or_404(
        ServiceSchedule.objects.select_related('site__client_id'),
        id=pk, site__assigned_contractor=request.user,
    )
    work = (
        CompleteWork.objects.filter(schedule=job, completed_by=request.user)
        .prefetch_related('work_completion_images').first()
    )
    site = _with_images(Site.objects.filter(pk=job.site_id)).first()
    today = timezone.localdate()
    context = {
        'job': job,
        'site': site,
        'work': work,
        'status': services.job_status(job),
        'overdue': job.status == 'SCHEDULED' and not work and job.scheduled_date < today,
        'duration': (work.check_out_time - work.check_in_time)
            if work and work.check_in_time and work.check_out_time else None,
    }
    return render(request, 'ops/contractor/job_detail.html', context)
