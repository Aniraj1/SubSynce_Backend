"""Client invoices: what the company bills its clients (revenue).

Kept apart from contractor invoices (cost). Rules mirror the backend client
invoice API: the client always comes from the chosen site, and only ISSUED
invoices can be edited or deleted. The builder's line items live in
ops.models; their sum is always written to ClientInvoice.amount, which the
profitability report reads once the invoice is PAID.

The backend API allows only ADMINISTRATOR here; the web frontend also lets
the Owner in, the same way every other staff screen does.
"""
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from client.model.clientmanage import Site
from invoice.model.invoicemanagement import ClientInvoice
from ops import services
from ops.access import staff_required
from ops.forms import ClientInvoiceForm, LineItemFormSet
from ops.models import ClientInvoiceExtra, ClientInvoiceLineItem, CompanyProfile

STATUSES = ("ISSUED", "PAID", "OVERDUE", "CANCELLED")

# Where each status can go next. PAID and CANCELLED are final.
NEXT_STATUSES = {
    "ISSUED": ("PAID", "OVERDUE", "CANCELLED"),
    "OVERDUE": ("PAID", "CANCELLED"),
    "PAID": (),
    "CANCELLED": (),
}

STATUS_MESSAGES = {
    "PAID": "marked as paid",
    "OVERDUE": "marked as overdue",
    "CANCELLED": "cancelled",
}


def _invoices():
    return ClientInvoice.objects.select_related("site", "client", "created_by")


@staff_required
def client_invoice_list_view(request):
    invoices = _invoices().order_by("-invoice_date", "-created_at")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status in STATUSES:
        invoices = invoices.filter(status=status)
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) | Q(site__name__icontains=query)
            | Q(client__first_name__icontains=query) | Q(client__last_name__icontains=query)
        )

    outstanding = Q(status__in=("ISSUED", "OVERDUE"))
    totals = ClientInvoice.objects.aggregate(
        outstanding_count=Count("id", filter=outstanding),
        outstanding_total=Sum("amount", filter=outstanding),
        paid_total=Sum("amount", filter=Q(status="PAID")),
        overdue_count=Count("id", filter=Q(status="OVERDUE")),
        overdue_total=Sum("amount", filter=Q(status="OVERDUE")),
    )
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "ops/client_invoices/list.html", {
        "page_obj": Paginator(invoices, 15).get_page(request.GET.get("page")),
        "status": status,
        "statuses": STATUSES,
        "query": query,
        "totals": totals,
        "querystring": params.urlencode(),
    })


def _save_builder(invoice, form, formset):
    """Write line items + notes/terms and keep the backend amount equal to their sum."""
    rows = [f.cleaned_data for f in formset.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
    invoice.line_items.all().delete()
    total = Decimal("0.00")
    for position, row in enumerate(rows):
        item = ClientInvoiceLineItem.objects.create(
            invoice=invoice, position=position, description=row["description"],
            quantity=row["quantity"], unit_price=row["unit_price"],
        )
        total += item.total
    ClientInvoiceExtra.objects.update_or_create(
        invoice=invoice, defaults={"notes": form.cleaned_data["notes"], "terms": form.cleaned_data["terms"]},
    )
    invoice.amount = total
    invoice.remarks = form.cleaned_data["notes"] or None
    invoice.save()


def _apply_header(invoice, data):
    for field in ("invoice_number", "site", "invoice_date", "service_period_start", "service_period_end", "gst"):
        setattr(invoice, field, data[field])
    invoice.client = data["site"].client_id


def _builder_context(form, formset, invoice=None):
    return {
        "header": form,
        "formset": formset,
        "invoice": invoice,
        "company": CompanyProfile.load(),
        "sites": form.fields["site"].queryset,
        "has_sites": form.fields["site"].queryset.exists(),
    }


def _site_from_query(value):
    """?site=<uuid> preselects a site (e.g. from the profitability report); bad ids are ignored."""
    try:
        return Site.objects.select_related("client_id").filter(pk=value).first() if value else None
    except (ValueError, ValidationError):
        return None


@staff_required
def client_invoice_create_view(request):
    if request.method == "POST":
        form = ClientInvoiceForm(request.POST)
        formset = LineItemFormSet(request.POST, prefix="items")
        if form.is_valid() and formset.is_valid():
            invoice = ClientInvoice(amount=Decimal("0.00"), created_by=request.user)
            _apply_header(invoice, form.cleaned_data)
            with transaction.atomic():
                invoice.save()
                _save_builder(invoice, form, formset)
            messages.success(request, f"Invoice {invoice.invoice_number} issued to {invoice.client.first_name}.")
            return redirect("ops:client_invoice_detail", pk=invoice.pk)
    else:
        initial = ClientInvoiceForm.initial_for_new(services.next_client_invoice_number())
        site = _site_from_query(request.GET.get("site"))
        items = [{"quantity": 1}]
        if site:
            initial["site"] = site.pk
            items = [{"description": f"Cleaning services · {site.name}", "quantity": 1, "unit_price": site.price}]
        form = ClientInvoiceForm(initial=initial)
        formset = LineItemFormSet(prefix="items", initial=items)
    return render(request, "ops/client_invoices/builder.html", _builder_context(form, formset))


@staff_required
def client_invoice_edit_view(request, pk):
    invoice = get_object_or_404(ClientInvoice, pk=pk)
    if invoice.status != "ISSUED":
        messages.error(request, "Only issued invoices can be edited.")
        return redirect("ops:client_invoice_detail", pk=invoice.pk)

    if request.method == "POST":
        form = ClientInvoiceForm(request.POST, instance=invoice)
        formset = LineItemFormSet(request.POST, prefix="items")
        if form.is_valid() and formset.is_valid():
            _apply_header(invoice, form.cleaned_data)
            with transaction.atomic():
                _save_builder(invoice, form, formset)
            messages.success(request, f"Invoice {invoice.invoice_number} updated.")
            return redirect("ops:client_invoice_detail", pk=invoice.pk)
    else:
        extra = getattr(invoice, "builder", None)
        form = ClientInvoiceForm(instance=invoice, initial={
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
    return render(request, "ops/client_invoices/builder.html", _builder_context(form, formset, invoice))


@staff_required
@require_POST
def client_invoice_delete_view(request, pk):
    invoice = get_object_or_404(ClientInvoice, pk=pk)
    if invoice.status != "ISSUED":
        messages.error(request, "Only issued invoices can be deleted. Cancel it instead.")
        return redirect("ops:client_invoice_detail", pk=invoice.pk)
    number = invoice.invoice_number
    invoice.delete()
    messages.success(request, f"Invoice {number} deleted.")
    return redirect("ops:client_invoices")


@staff_required
def client_invoice_detail_view(request, pk):
    invoice = get_object_or_404(_invoices(), pk=pk)
    return render(request, "ops/client_invoices/detail.html", {
        "invoice": invoice,
        "items": invoice.line_items.all(),
        "extra": getattr(invoice, "builder", None),
        "totals": services.invoice_totals(invoice),
        "next_statuses": NEXT_STATUSES[invoice.status],
        "work": services.completed_work_value(invoice.site, invoice.service_period_start, invoice.service_period_end),
    })


@staff_required
@require_POST
def client_invoice_status_view(request, pk):
    invoice = get_object_or_404(ClientInvoice, pk=pk)
    new_status = request.POST.get("status", "")
    if new_status not in NEXT_STATUSES[invoice.status]:
        messages.error(request, f"A {invoice.status.lower()} invoice can't be {STATUS_MESSAGES.get(new_status, 'changed that way')}.")
        return redirect("ops:client_invoice_detail", pk=invoice.pk)
    with transaction.atomic():
        invoice.status = new_status
        invoice.save()
        ClientInvoiceExtra.objects.update_or_create(
            invoice=invoice, defaults={"status_changed_by": request.user, "status_changed_at": timezone.now()},
        )
    messages.success(request, f"Invoice {invoice.invoice_number} {STATUS_MESSAGES[new_status]}.")
    return redirect("ops:client_invoice_detail", pk=invoice.pk)


@staff_required
def client_invoice_print_view(request, pk):
    invoice = get_object_or_404(_invoices(), pk=pk)
    return render(request, "ops/client_invoices/print.html", {
        "invoice": invoice,
        "items": list(invoice.line_items.all()),
        "extra": getattr(invoice, "builder", None),
        "totals": services.invoice_totals(invoice),
        "company": CompanyProfile.load(),
    })
