from django.urls import path

from invoice.api.views import user_views

urlpatterns = [
    path("invoices/", user_views.InvoiceView.as_view(), name="InvoiceView"),
    path("invoices/earnings/", user_views.TotalEarningsView.as_view(), name="TotalEarningsView"),
    path("invoice/<str:id>/", user_views.DetailInvoiceView.as_view(), name="DetailInvoiceView"),
]