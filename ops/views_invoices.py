"""Contractor invoices: builder, list, verification and print (brief 3.7, 3.8).

Rules mirror the backend invoice API: contractors create invoices only for
sites assigned to them, and only administrators (plus the Owner) decide.
The builder's line items live in ops.models; their sum is always written to
ContractorInvoice.amount.
"""
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from invoice.model.invoicemanagement import ContractorInvoice
from ops import services
from ops.access import CONTRACTOR, STAFF_ROLES, contractor_required, is_staff_user, role_required, staff_required
from ops.forms import DecisionForm, InvoiceHeaderForm, LineItemFormSet
from ops.models import CompanyProfile, InvoiceExtra, InvoiceLineItem

any_role = role_required(CONTRACTOR, *STAFF_ROLES)


def _visible_invoices(user):
    invoices = ContractorInvoice.objects.select_related("site", "created_by", "verified_by")
    return invoices if is_staff_user(user) else invoices.filter(created_by=user)


def _get_invoice(request, pk):
    invoice = _visible_invoices(request.user).filter(pk=pk).first()
    if not invoice:
        raise Http404
    return invoice


@any_role
def invoice_list_view(request):
    invoices = _visible_invoices(request.user).order_by("-invoice_date", "-created_at")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status in ("PENDING", "APPROVED", "REJECTED"):
        invoices = invoices.filter(status=status)
    # Date range on the invoice date; either end can be left open.
    start = services.parse_date(request.GET.get("start"))
    end = services.parse_date(request.GET.get("end"))
    range_error = None
    if start and end and start > end:
        range_error = "The From date must be on or before the To date."
        start = end = None
    if start:
        invoices = invoices.filter(invoice_date__gte=start)
    if end:
        invoices = invoices.filter(invoice_date__lte=end)
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) | Q(site__name__icontains=query) | Q(created_by__username__icontains=query)
        )

    base = _visible_invoices(request.user)
    totals = base.aggregate(
        pending_count=Count("id", filter=Q(status="PENDING")),
        pending_total=Sum("amount", filter=Q(status="PENDING")),
        approved_total=Sum("amount", filter=Q(status="APPROVED")),
        rejected_count=Count("id", filter=Q(status="REJECTED")),
    )
    approved_count = base.filter(status="APPROVED").count()
    totals["approved_hint"] = f"From {approved_count} approved invoice{'' if approved_count == 1 else 's'}"
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "ops/invoices/list.html", {
        "page_obj": Paginator(invoices, 15).get_page(request.GET.get("page")),
        "status": status,
        "query": query,
        "start": start,
        "end": end,
        "range_error": range_error,
        "totals": totals,
        "querystring": params.urlencode(),
        "chart": _earnings_chart(request.user) if request.user.role == CONTRACTOR else None,
    })


def _compact_money(value):
    """Short axis label: $950, $12.5k, $1.2M."""
    value = float(value)
    for limit, suffix in ((1_000_000, "M"), (1_000, "k")):
        if value >= limit:
            return f"${value / limit:.1f}".rstrip("0").rstrip(".") + suffix
    return f"${value:.0f}"


def _earnings_chart(user):
    """Data for the My Invoices line graph: approved earnings per month over the last 12 months.

    Drawn as a stretched inline SVG (viewBox 0 0 1000 100, preserveAspectRatio="none") so it
    needs no chart library. Each month-to-month segment is green when earnings rose, red when
    they fell and grey when flat; `change` compares this month with last month the same way.
    """
    rows = services.monthly_approved_earnings(user)
    peak = max((r["total"] for r in rows), default=Decimal("0"))
    top, bottom = 6, 96
    step = 1000 / (len(rows) - 1)
    points = []
    for i, r in enumerate(rows):
        y = bottom - (float(r["total"] / peak) * (bottom - top) if peak else 0)
        points.append({**r, "x": round(i * step, 1), "y": round(y, 1)})
    segments = []
    for prev, cur in zip(points, points[1:]):
        trend = "up" if cur["total"] > prev["total"] else "down" if cur["total"] < prev["total"] else "flat"
        segments.append({"x1": prev["x"], "y1": prev["y"], "x2": cur["x"], "y2": cur["y"], "trend": trend})
    change = rows[-1]["total"] - rows[-2]["total"]
    return {
        "points": points,
        "segments": segments,
        "peak": peak,
        "scale": [_compact_money(peak), _compact_money(peak / 2), "$0"],
        "year_total": sum((r["total"] for r in rows), Decimal("0")),
        "this_month": rows[-1],
        "last_month": rows[-2],
        "change": change,
        "change_abs": abs(change),
        "has_data": bool(peak),
    }


def _save_builder(invoice, header, formset):
    """Write line items + notes/terms and keep the backend amount equal to their sum."""
    rows = [f.cleaned_data for f in formset.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
    invoice.line_items.all().delete()
    total = Decimal("0.00")
    for position, row in enumerate(rows):
        item = InvoiceLineItem.objects.create(
            invoice=invoice, position=position, description=row["description"],
            quantity=row["quantity"], unit_price=row["unit_price"],
        )
        total += item.total
    InvoiceExtra.objects.update_or_create(
        invoice=invoice, defaults={"notes": header.cleaned_data["notes"], "terms": header.cleaned_data["terms"]},
    )
    invoice.amount = total
    # remarks is the backend's free-text field; mirror the notes there so the
    # API shows them too.
    invoice.remarks = header.cleaned_data["notes"] or None
    invoice.save()


def _builder_context(header, formset, invoice=None):
    return {
        "header": header,
        "formset": formset,
        "invoice": invoice,
        "company": CompanyProfile.load(),
        "has_sites": header.fields["site"].queryset.exists(),
    }


@contractor_required
def invoice_create_view(request):
    if request.method == "POST":
        header = InvoiceHeaderForm(request.POST, contractor=request.user)
        formset = LineItemFormSet(request.POST, prefix="items")
        if header.is_valid() and formset.is_valid():
            data = header.cleaned_data
            with transaction.atomic():
                invoice = ContractorInvoice.objects.create(
                    invoice_number=data["invoice_number"],
                    site=data["site"],
                    invoice_date=data["invoice_date"],
                    service_period_start=data["service_period_start"],
                    service_period_end=data["service_period_end"],
                    gst=data["gst"],
                    amount=Decimal("0.00"),
                    created_by=request.user,
                )
                _save_builder(invoice, header, formset)
            messages.success(request, f"Invoice {invoice.invoice_number} submitted for verification.")
            return redirect("ops:invoice_detail", pk=invoice.pk)
    else:
        header = InvoiceHeaderForm(
            contractor=request.user,
            initial=InvoiceHeaderForm.initial_for_new(services.next_invoice_number()),
        )
        formset = LineItemFormSet(prefix="items", initial=[{"quantity": 1}])
    return render(request, "ops/invoices/builder.html", _builder_context(header, formset))


@contractor_required
def invoice_edit_view(request, pk):
    invoice = get_object_or_404(ContractorInvoice, pk=pk, created_by=request.user)
    if invoice.status != "PENDING":
        messages.error(request, "Only pending invoices can be edited.")
        return redirect("ops:invoice_detail", pk=invoice.pk)

    if request.method == "POST":
        header = InvoiceHeaderForm(request.POST, contractor=request.user, instance=invoice)
        formset = LineItemFormSet(request.POST, prefix="items")
        if header.is_valid() and formset.is_valid():
            data = header.cleaned_data
            with transaction.atomic():
                for field in ("invoice_number", "site", "invoice_date", "service_period_start", "service_period_end", "gst"):
                    setattr(invoice, field, data[field])
                _save_builder(invoice, header, formset)
            messages.success(request, f"Invoice {invoice.invoice_number} updated.")
            return redirect("ops:invoice_detail", pk=invoice.pk)
    else:
        extra = getattr(invoice, "builder", None)
        header = InvoiceHeaderForm(contractor=request.user, instance=invoice, initial={
            "invoice_number": invoice.invoice_number,
            "site": invoice.site_id,
            "invoice_date": invoice.invoice_date,
            "service_period_start": invoice.service_period_start,
            "service_period_end": invoice.service_period_end,
            "notes": extra.notes if extra else (invoice.remarks or ""),
            "terms": extra.terms if extra else "",
            "gst": invoice.gst,
        })
        items = [
            {"description": i.description, "quantity": i.quantity, "unit_price": i.unit_price}
            for i in invoice.line_items.all()
        ] or [{"description": "Cleaning services", "quantity": 1, "unit_price": invoice.amount}]
        formset = LineItemFormSet(prefix="items", initial=items)
    return render(request, "ops/invoices/builder.html", _builder_context(header, formset, invoice))


@contractor_required
@require_POST
def invoice_delete_view(request, pk):
    invoice = get_object_or_404(ContractorInvoice, pk=pk, created_by=request.user)
    if invoice.status != "PENDING":
        messages.error(request, "Only pending invoices can be deleted.")
        return redirect("ops:invoice_detail", pk=invoice.pk)
    number = invoice.invoice_number
    invoice.delete()
    messages.success(request, f"Invoice {number} deleted.")
    return redirect("ops:invoices")


@any_role
def invoice_detail_view(request, pk):
    invoice = _get_invoice(request, pk)
    context = {
        "invoice": invoice,
        "items": invoice.line_items.all(),
        "extra": getattr(invoice, "builder", None),
        "totals": services.invoice_totals(invoice),
        "decision_form": DecisionForm(),
    }
    if is_staff_user(request.user):
        context["check"] = services.verify_invoice(invoice)
    return render(request, "ops/invoices/detail.html", context)


@staff_required
@require_POST
def invoice_decide_view(request, pk):
    invoice = get_object_or_404(ContractorInvoice, pk=pk)
    if invoice.status != "PENDING":
        messages.error(request, "This invoice has already been decided.")
        return redirect("ops:invoice_detail", pk=invoice.pk)
    form = DecisionForm(request.POST)
    if not form.is_valid():
        return render(request, "ops/invoices/detail.html", {
            "invoice": invoice,
            "items": invoice.line_items.all(),
            "extra": getattr(invoice, "builder", None),
            "totals": services.invoice_totals(invoice),
            "decision_form": form,
            "check": services.verify_invoice(invoice),
        }, status=400)
    invoice.status = form.cleaned_data["decision"]
    invoice.verification_notes = form.cleaned_data["verification_notes"].strip() or None
    invoice.verified_by = request.user
    invoice.verified_at = timezone.now()
    invoice.save()
    verb = "approved" if invoice.status == "APPROVED" else "rejected"
    messages.success(request, f"Invoice {invoice.invoice_number} {verb}.")
    return redirect("ops:invoice_detail", pk=invoice.pk)


@any_role
def invoice_print_view(request, pk):
    invoice = _get_invoice(request, pk)
    items = list(invoice.line_items.all())
    return render(request, "ops/invoices/print.html", {
        "invoice": invoice,
        "items": items,
        "extra": getattr(invoice, "builder", None),
        "totals": services.invoice_totals(invoice),
        "company": CompanyProfile.load(),
    })
