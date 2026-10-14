"""Financial reporting: profit per site and per client (brief 3.9)."""
import csv

from django.http import HttpResponse
from django.shortcuts import render

from ops import services
from ops.access import staff_required


@staff_required
def profitability_view(request):
    start = services.parse_date(request.GET.get("start"))
    end = services.parse_date(request.GET.get("end"))
    error = None
    if start and end and start > end:
        error = "Start date must be on or before the end date."
        start = end = None
    group = "client" if request.GET.get("group") == "client" else "site"

    rows = services.site_profitability(start, end)
    totals = services.totals_for(rows)

    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="site-profitability.csv"'
        writer = csv.writer(response)
        writer.writerow(["Site", "Client", "Completed jobs", "Work value", "Revenue", "Cost", "Profit", "Margin"])
        for r in rows:
            client = f"{r['client'].first_name} {r['client'].last_name or ''}".strip()
            margin = f"{r['margin']:.1%}" if r["margin"] is not None else ""
            writer.writerow([r["site"].name, client, r["completed"], r["work_value"], r["revenue"], r["cost"], r["profit"], margin])
        return response

    params = request.GET.copy()
    params.pop("format", None)
    return render(request, "ops/reports/profitability.html", {
        "rows": sorted(rows, key=lambda r: r["profit"], reverse=True),
        "clients": services.group_by_client(rows) if group == "client" else None,
        "totals": totals,
        "group": group,
        "start": start,
        "end": end,
        "error": error,
        "csv_query": (params.urlencode() + "&" if params else "") + "format=csv",
    })
