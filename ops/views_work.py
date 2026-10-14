"""Work completion screens (brief 3.6).

Contractors see their jobs and past work records. Staff see the completion
log.
"""
from datetime import date

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from ops import services
from ops.access import contractor_required, is_staff_user, role_required, staff_required, CONTRACTOR, STAFF_ROLES
from work.model.workcomplete import CompleteWork


@contractor_required
def my_jobs_view(request):
    today = date.today()
    jobs = services.contractor_jobs(request.user).select_related("work_completion")
    to_do = jobs.filter(status="SCHEDULED", work_completion__isnull=True, scheduled_date__lte=today)
    upcoming = jobs.filter(status="SCHEDULED", work_completion__isnull=True, scheduled_date__gt=today)
    history = Paginator(
        CompleteWork.objects.filter(completed_by=request.user)
        .exclude(status="IN_PROGRESS")
        .select_related("schedule__site")
        .order_by("-check_in_time"),
        10,
    ).get_page(request.GET.get("page"))
    return render(request, "ops/work/my_jobs.html", {
        "today": today,
        "to_do": to_do.order_by("scheduled_date", "scheduled_time"),
        "upcoming": upcoming.order_by("scheduled_date", "scheduled_time")[:20],
        "history": history,
    })


@role_required(CONTRACTOR, *STAFF_ROLES)
def work_detail_view(request, work_id):
    work = get_object_or_404(
        CompleteWork.objects.select_related("schedule__site__client_id", "completed_by")
        .prefetch_related("work_completion_images"),
        id=work_id,
    )
    if not is_staff_user(request.user) and work.completed_by_id != request.user.id:
        raise Http404
    duration = None
    if work.check_in_time and work.check_out_time:
        duration = work.check_out_time - work.check_in_time
    return render(request, "ops/work/detail.html", {"work": work, "duration": duration})


@staff_required
def completions_view(request):
    records = CompleteWork.objects.select_related("schedule__site", "completed_by").order_by("-check_in_time")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    start = services.parse_date(request.GET.get("start"))
    end = services.parse_date(request.GET.get("end"))
    if status in ("IN_PROGRESS", "COMPLETED", "MISSED"):
        records = records.filter(status=status)
    if query:
        records = records.filter(
            Q(schedule__site__name__icontains=query)
            | Q(completed_by__username__icontains=query)
            | Q(completion_notes__icontains=query)
        )
    if start:
        records = records.filter(schedule__scheduled_date__gte=start)
    if end:
        records = records.filter(schedule__scheduled_date__lte=end)

    page = Paginator(records, 15).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "ops/work/completions.html", {
        "page_obj": page,
        "status": status,
        "query": query,
        "start": start,
        "end": end,
        "querystring": params.urlencode(),
    })
