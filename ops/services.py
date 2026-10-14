"""Read-only figures for the web frontend.

These mirror the backend's own calculations (dashboard/api/views) so the web
screens and the API agree. Nothing here writes to the database.
"""
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import models
from django.db.models import Sum

from authuser.model.user import User
from client.model.clientmanage import Client, Site
from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from schedule.model.cleaningschedule import ServiceSchedule
from work.model.workcomplete import CompleteWork

ZERO = Decimal("0.00")

# Australian GST. The backend only stores whether an invoice includes GST
# (invoice.gst); amount stays the ex-GST total of the line items, so reports
# and verification compare like with like.
GST_RATE = Decimal("0.10")


def _total(queryset):
    return queryset.aggregate(total=Sum("amount"))["total"] or ZERO


def parse_date(value):
    """ISO date string -> date, or None when blank/invalid."""
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def admin_summary(start=None, end=None):
    """Counts and money for the staff dashboard, optionally within a date range."""
    schedules = ServiceSchedule.objects.all()
    work = CompleteWork.objects.all()
    contractor_invoices = ContractorInvoice.objects.all()
    client_invoices = ClientInvoice.objects.all()

    if start:
        schedules = schedules.filter(scheduled_date__gte=start)
        work = work.filter(schedule__scheduled_date__gte=start)
        contractor_invoices = contractor_invoices.filter(invoice_date__gte=start)
        client_invoices = client_invoices.filter(invoice_date__gte=start)
    if end:
        schedules = schedules.filter(scheduled_date__lte=end)
        work = work.filter(schedule__scheduled_date__lte=end)
        contractor_invoices = contractor_invoices.filter(invoice_date__lte=end)
        client_invoices = client_invoices.filter(invoice_date__lte=end)

    revenue = _total(client_invoices.filter(status="PAID"))
    cost = _total(contractor_invoices.filter(status="APPROVED"))
    services_total = schedules.count()
    completed = work.filter(status="COMPLETED").count()

    return {
        "clients": Client.objects.count(),
        "sites": Site.objects.count(),
        "contractors": User.objects.filter(role="CONTRACTOR", deleted_at__isnull=True).count(),
        "services": {
            "total": services_total,
            # Clock-out doesn't change the schedule's own status, so a job
            # counts as "scheduled" only while it has no work record yet.
            "scheduled": schedules.filter(status="SCHEDULED", work_completion__isnull=True).count(),
            "completed": completed,
            "in_progress": work.filter(status="IN_PROGRESS").count(),
            "missed": schedules.filter(status="MISSED").count() + work.filter(status="MISSED").exclude(schedule__status="MISSED").count(),
            "cancelled": schedules.filter(status="CANCELLED").count(),
            "completion_rate": (completed / services_total) if services_total else None,
        },
        "contractor_invoices": {
            "pending": contractor_invoices.filter(status="PENDING").count(),
            "approved": contractor_invoices.filter(status="APPROVED").count(),
            "rejected": contractor_invoices.filter(status="REJECTED").count(),
        },
        "client_invoices": {
            "issued": client_invoices.filter(status="ISSUED").count(),
            "paid": client_invoices.filter(status="PAID").count(),
            "overdue": client_invoices.filter(status="OVERDUE").count(),
        },
        "revenue": revenue,
        "cost": cost,
        "profit": revenue - cost,
        "margin": ((revenue - cost) / revenue) if revenue else None,
    }


def job_status(schedule):
    """What a job's status really is: its work record wins over the schedule's own status."""
    work = getattr(schedule, "work_completion", None)
    if schedule.status in ("MISSED", "CANCELLED"):
        return schedule.status
    return work.status if work else schedule.status


def todays_schedule(day=None):
    day = day or date.today()
    return (
        ServiceSchedule.objects.filter(scheduled_date=day)
        .select_related("site", "site__assigned_contractor", "work_completion")
        .order_by("scheduled_time")
    )


def contractor_jobs(user):
    """Schedules on sites assigned to this contractor."""
    return ServiceSchedule.objects.filter(site__assigned_contractor=user).select_related("site")


def monthly_approved_earnings(user, months=12, today=None):
    """Approved invoice totals per month (by invoice date) for the last `months` months, oldest first."""
    today = today or date.today()
    starts = []
    year, month = today.year, today.month
    for _ in range(months):
        starts.append(date(year, month, 1))
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    starts.reverse()
    totals = {
        (row["invoice_date__year"], row["invoice_date__month"]): row["total"]
        for row in ContractorInvoice.objects.filter(
            created_by=user, status="APPROVED", invoice_date__gte=starts[0]
        ).values("invoice_date__year", "invoice_date__month").annotate(total=Sum("amount"))
    }
    return [{"month": s, "total": totals.get((s.year, s.month)) or ZERO} for s in starts]


def contractor_dashboard(user, start=None, end=None):
    """
    The ContractorDashboard API's figures (dashboard/api/views/user_views.py,
    GET /api/v1/user/dashboard/), same queries and keys, for the session-based portal.
    Only this contractor's sites, schedules, work and invoices are counted.
    """
    sites = Site.objects.filter(assigned_contractor=user)
    schedules = ServiceSchedule.objects.filter(site__assigned_contractor=user)
    work = CompleteWork.objects.filter(completed_by=user)
    invoices = ContractorInvoice.objects.filter(created_by=user)
    if start:
        schedules = schedules.filter(scheduled_date__gte=start)
        work = work.filter(schedule__scheduled_date__gte=start)
        invoices = invoices.filter(invoice_date__gte=start)
    if end:
        schedules = schedules.filter(scheduled_date__lte=end)
        work = work.filter(schedule__scheduled_date__lte=end)
        invoices = invoices.filter(invoice_date__lte=end)
    approved = invoices.filter(status="APPROVED")
    return {
        "sites": {"assigned": sites.count()},
        "services": {
            "scheduled": schedules.filter(status="SCHEDULED").count(),
            "completed": work.filter(status="COMPLETED").count(),
            "in_progress": work.filter(status="IN_PROGRESS").count(),
            "missed": work.filter(status="MISSED").count(),
            "cancelled": schedules.filter(status="CANCELLED").count(),
        },
        "invoices": {
            "pending": invoices.filter(status="PENDING").count(),
            "approved": approved.count(),
            "rejected": invoices.filter(status="REJECTED").count(),
        },
        "earnings": {
            "approved_invoice_count": approved.count(),
            "total_earnings": _total(approved),
        },
    }


def contractor_summary(user, today=None):
    today = today or date.today()
    jobs = contractor_jobs(user)
    work = CompleteWork.objects.filter(completed_by=user)
    invoices = ContractorInvoice.objects.filter(created_by=user)
    return {
        "today": jobs.filter(scheduled_date=today).select_related("work_completion").order_by("scheduled_time"),
        "upcoming": jobs.filter(
            scheduled_date__gt=today,
            scheduled_date__lte=today + timedelta(days=14),
            status="SCHEDULED",
        ).order_by("scheduled_date", "scheduled_time")[:10],
        "completed_count": work.filter(status="COMPLETED").count(),
        "sites": Site.objects.filter(assigned_contractor=user).count(),
        "invoices": {
            "pending": invoices.filter(status="PENDING").count(),
            "approved": invoices.filter(status="APPROVED").count(),
            "rejected": invoices.filter(status="REJECTED").count(),
        },
        "earnings": _total(invoices.filter(status="APPROVED")),
    }


# --- Invoice verification (brief 3.8) ---------------------------------------
#
# The backend's verify endpoint only records approve/reject. These checks
# compare an invoice against recorded work so the reviewer sees mismatches
# before deciding. They are advisory and never saved.

FLAG_MESSAGES = {
    "NO_RECORDED_WORK": "No completed services are recorded for this site and period.",
    "MISSING_VISITS": "{recorded} of {scheduled} scheduled services were recorded as completed.",
    "WRONG_CONTRACTOR": "Work at this site in this period was recorded by another contractor.",
    "QUANTITY_EXCEEDS_WORK": "The invoice bills {billed} services but only {recorded} were recorded.",
    "DUPLICATE_PERIOD": "Another invoice from this contractor already covers this site and period ({numbers}).",
}


def verify_invoice(invoice):
    """Return the evidence and flags for one contractor invoice."""
    period = [invoice.service_period_start, invoice.service_period_end]
    completions = (
        CompleteWork.objects.filter(
            schedule__site=invoice.site,
            completed_by=invoice.created_by,
            status="COMPLETED",
            schedule__scheduled_date__range=period,
        )
        .select_related("schedule")
        .order_by("schedule__scheduled_date")
    )
    scheduled = (
        ServiceSchedule.objects.filter(site=invoice.site, scheduled_date__range=period)
        .exclude(status="CANCELLED")
        .select_related("work_completion")
        .order_by("scheduled_date", "scheduled_time")
    )
    others = (
        CompleteWork.objects.filter(schedule__site=invoice.site, schedule__scheduled_date__range=period)
        .exclude(completed_by=invoice.created_by)
        .select_related("completed_by")
    )
    overlapping = (
        ContractorInvoice.objects.filter(
            site=invoice.site,
            created_by=invoice.created_by,
            service_period_start__lte=invoice.service_period_end,
            service_period_end__gte=invoice.service_period_start,
        )
        .exclude(pk=invoice.pk)
        .exclude(status="REJECTED")
    )

    recorded = completions.count()
    scheduled_count = scheduled.count()
    billed = sum((item.quantity for item in invoice.line_items.all()), Decimal("0"))

    flags = []
    if recorded == 0:
        flags.append(("NO_RECORDED_WORK", FLAG_MESSAGES["NO_RECORDED_WORK"]))
    elif scheduled_count > recorded:
        flags.append(("MISSING_VISITS", FLAG_MESSAGES["MISSING_VISITS"].format(recorded=recorded, scheduled=scheduled_count)))
    if others.exists():
        flags.append(("WRONG_CONTRACTOR", FLAG_MESSAGES["WRONG_CONTRACTOR"]))
    if billed and billed > recorded:
        flags.append(("QUANTITY_EXCEEDS_WORK", FLAG_MESSAGES["QUANTITY_EXCEEDS_WORK"].format(
            billed=billed.normalize(), recorded=recorded)))
    if overlapping.exists():
        numbers = ", ".join(overlapping.values_list("invoice_number", flat=True))
        flags.append(("DUPLICATE_PERIOD", FLAG_MESSAGES["DUPLICATE_PERIOD"].format(numbers=numbers)))

    expected = invoice.site.price * recorded
    return {
        "completions": completions,
        "scheduled": scheduled,
        "other_work": others,
        "recorded": recorded,
        "scheduled_count": scheduled_count,
        "billed_quantity": billed,
        "client_value": expected,
        "flags": flags,
    }


def invoice_totals(invoice):
    """Subtotal, GST and total payable for an invoice; gst is None when it's not included."""
    subtotal = invoice.amount or ZERO
    gst = (subtotal * GST_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if invoice.gst else None
    return {"subtotal": subtotal, "gst": gst, "total": subtotal + (gst or ZERO)}


def _next_number(model, prefix, today=None):
    year = (today or date.today()).year
    prefix = f"{prefix}-{year}-"
    highest = 0
    # global_objects includes soft-deleted invoices, which still hold their
    # number in the unique index.
    numbers = model.global_objects.filter(invoice_number__startswith=prefix)
    for number in numbers.values_list("invoice_number", flat=True):
        tail = number[len(prefix):]
        if tail.isdigit():
            highest = max(highest, int(tail))
    return f"{prefix}{highest + 1:03d}"


def next_invoice_number(today=None):
    """Next free INV-YYYY-### number for a contractor invoice."""
    return _next_number(ContractorInvoice, "INV", today)


def next_client_invoice_number(today=None):
    """Next free CINV-YYYY-### number for an invoice sent to a client."""
    return _next_number(ClientInvoice, "CINV", today)


def completed_work_value(site, start, end):
    """Completed jobs at a site in a period and what they are worth at the site price."""
    jobs = CompleteWork.objects.filter(
        status="COMPLETED", schedule__site=site,
        schedule__scheduled_date__gte=start, schedule__scheduled_date__lte=end,
    ).count()
    return {"jobs": jobs, "value": site.price * jobs}


# --- Financial reporting (brief 3.9) -----------------------------------------

def site_profitability(start=None, end=None):
    """Per-site revenue, cost and profit.

    Revenue and cost use the same rule as the backend's profit report:
    revenue = PAID client invoices, cost = APPROVED contractor invoices,
    filtered by invoice date. "Work value" is completed jobs x site price,
    which shows work done but not yet billed to the client.
    """
    client_inv = ClientInvoice.objects.filter(status="PAID")
    contractor_inv = ContractorInvoice.objects.filter(status="APPROVED")
    work = CompleteWork.objects.filter(status="COMPLETED")
    if start:
        client_inv = client_inv.filter(invoice_date__gte=start)
        contractor_inv = contractor_inv.filter(invoice_date__gte=start)
        work = work.filter(schedule__scheduled_date__gte=start)
    if end:
        client_inv = client_inv.filter(invoice_date__lte=end)
        contractor_inv = contractor_inv.filter(invoice_date__lte=end)
        work = work.filter(schedule__scheduled_date__lte=end)

    revenue = dict(client_inv.values("site").annotate(t=Sum("amount")).values_list("site", "t"))
    cost = dict(contractor_inv.values("site").annotate(t=Sum("amount")).values_list("site", "t"))
    jobs = dict(work.values("schedule__site").annotate(n=models.Count("id")).values_list("schedule__site", "n"))

    rows = []
    for site in Site.objects.select_related("client_id", "assigned_contractor").order_by("name"):
        r = revenue.get(site.id) or ZERO
        c = cost.get(site.id) or ZERO
        n = jobs.get(site.id, 0)
        rows.append({
            "site": site,
            "client": site.client_id,
            "completed": n,
            "work_value": site.price * n,
            "revenue": r,
            "cost": c,
            "profit": r - c,
            "margin": ((r - c) / r) if r else None,
        })
    return rows


def totals_for(rows):
    revenue = sum((r["revenue"] for r in rows), ZERO)
    cost = sum((r["cost"] for r in rows), ZERO)
    return {
        "completed": sum(r["completed"] for r in rows),
        "work_value": sum((r["work_value"] for r in rows), ZERO),
        "revenue": revenue,
        "cost": cost,
        "profit": revenue - cost,
        "margin": ((revenue - cost) / revenue) if revenue else None,
    }


def group_by_client(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["client"].pk, {"client": row["client"], "rows": []})["rows"].append(row)
    result = []
    for g in groups.values():
        result.append({"client": g["client"], "sites": len(g["rows"]), **totals_for(g["rows"])})
    return sorted(result, key=lambda g: g["profit"], reverse=True)
