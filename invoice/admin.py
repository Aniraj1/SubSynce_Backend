from django.contrib import admin
from invoice.model.invoicemanagement import ContractorInvoice, ClientInvoice

# Register your models here.
admin.site.register(ContractorInvoice)
admin.site.register(ClientInvoice)
