from django.urls import path

from invoice.api.views import admin_views

urlpatterns = [
    path("invoices/", admin_views.AllInvoiceAdminView.as_view(), name="AllInvoiceAdminView"),
    path("invoice/<str:id>/", admin_views.GetDetailInvoiceAdminView.as_view(), name="GetDetailInvoiceAdminView"),
    path("invoice/<str:id>/verify/", admin_views.InvoiceVerificationView.as_view(), name="InvoiceVerificationView"),
]