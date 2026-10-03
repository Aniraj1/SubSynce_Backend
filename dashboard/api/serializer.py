from rest_framework import serializers

from authuser.model.user import User
from client.model.clientmanage import Site, Client
from invoice.model.invoicemanagement import ContractorInvoice, ClientInvoice
from work.model.workcomplete import CompleteWork, WorkCompleteImage



class AdminDashboardSerializer(serializers.Serializer):
	clients = serializers.DictField()
	sites = serializers.DictField()
	contractors = serializers.DictField()
	services = serializers.DictField()
	contractor_invoices = serializers.DictField()
	client_invoices = serializers.DictField()
	profitability = serializers.DictField()

class ContractorDashboardSerializer(serializers.Serializer):
	sites = serializers.DictField()
	services = serializers.DictField()
	invoices = serializers.DictField()
	earnings = serializers.DictField()


