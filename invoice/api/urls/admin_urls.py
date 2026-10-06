from django.urls import path

from invoice.api.views import admin_views

urlpatterns = [
    path("invoices/", admin_views.AllInvoiceAdminView.as_view(), name="AllInvoiceAdminView"),
    path("invoice/<str:id>/", admin_views.GetDetailInvoiceAdminView.as_view(), name="GetDetailInvoiceAdminView"),
    path("invoice/<str:id>/verify/", admin_views.InvoiceVerificationView.as_view(), name="InvoiceVerificationView"),
    path("expenditure/", admin_views.TotalExpenditureAdminView.as_view(), name="TotalExpenditureAdminView"),
    path("client-invoice/", admin_views.ClientInvoiceViews.as_view(), name="ClientInvoiceViews"),
    path("client-invoice/<str:id>/", admin_views.DetailClientInvoiceView.as_view(), name="DetailClientInvoiceView"),
    path("client-invoice/<str:id>/status/", admin_views.ClientInvoiceStatusUpdateView.as_view(), name="ClientInvoiceStatusUpdateView"),
    path("revenue-report/", admin_views.RevenueReportView.as_view(), name="RevenueReportView"),
    path("profit-report/", admin_views.ProfitReportView.as_view(), name="ProfitReportView"),
]