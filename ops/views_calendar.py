"""Calendar of scheduled jobs: month grid, day agenda, role-scoped.

/calendar/      staff: every job, filter by contractor, site and status
/calendar/mine/ contractor: jobs on their assigned sites
"""
import calendar
from datetime import date, timedelta

from django.shortcuts import render

from authuser.model.user import User
from client.model.clientmanage import Site
from ops import services
from ops.access import contractor_required, staff_required
from schedule.model.cleaningschedule import ServiceSchedule

STATUSES = ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "MISSED", "CANCELLED"]
MAX_CHIPS = 3


def _month_from(value, today):
    try:
        year, month = (int(part) for part in (value or "").split("-"))
        return date(year, month, 1)
    except ValueError:
        return today.replace(day=1)


def _shift(first, months):
    index = first.year * 12 + first.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


def _render(request, jobs, *, scope, filters=None, extra=None):
    today = date.today()
    first = _month_from(request.GET.get("month"), today)
    grid_start = first - timedelta(days=first.weekday())
    last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
    grid_end = last + timedelta(days=6 - last.weekday())

    jobs = (
        jobs.filter(scheduled_date__range=[grid_start, grid_end])
        .select_related("site", "site__assigned_contractor", "work_completion")
        .order_by("scheduled_date", "scheduled_time")
    )
    status = request.GET.get("status", "")
    by_day = {}
    for job in jobs:
        job.display_status = services.job_status(job)
        if status and job.display_status != status:
            continue
        by_day.setdefault(job.scheduled_date, []).append(job)

    weeks, day = [], grid_start
    while day <= grid_end:
        week = []
        for _ in range(7):
            items = by_day.get(day, [])
            week.append({
                "date": day,
                "in_month": day.month == first.month,
                "is_today": day == today,
                "jobs": items[:MAX_CHIPS],
                "more": max(len(items) - MAX_CHIPS, 0),
                "count": len(items),
            })
            day += timedelta(days=1)
        weeks.append(week)

    selected = services.parse_date(request.GET.get("day"))
    if not selected or not (grid_start <= selected <= grid_end):
        selected = today if first <= today <= last else first

    params = request.GET.copy()
    for key in ("month", "day"):
        params.pop(key, None)
    context = {
        "scope": scope,
        "month": first,
        "prev_month": _shift(first, -1),
        "next_month": _shift(first, 1),
        "weeks": weeks,
        "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "selected": selected,
        "agenda": by_day.get(selected, []),
        "month_days": [(d, by_day[d]) for d in sorted(by_day) if d.month == first.month],
        "status": status,
        "statuses": STATUSES,
        "filter_query": params.urlencode(),
        "today": today,
    }
    context.update(filters or {})
    context.update(extra or {})
    return render(request, "ops/calendar/month.html", context)


@staff_required
def calendar_view(request):
    jobs = ServiceSchedule.objects.all()
    contractor = request.GET.get("contractor", "")
    site = request.GET.get("site", "")
    if contractor:
        jobs = jobs.filter(site__assigned_contractor_id=contractor)
    if site:
        jobs = jobs.filter(site_id=site)
    return _render(request, jobs, scope="all", filters={
        "contractors": User.objects.filter(role="CONTRACTOR").order_by("username"),
        "sites": Site.objects.order_by("name"),
        "contractor": contractor,
        "site": site,
    })


@contractor_required
def my_calendar_view(request):
    return _render(request, services.contractor_jobs(request.user), scope="mine")
