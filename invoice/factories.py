import factory
from faker import Faker
from authuser.factories import UserFactory
from client.factories import SiteFactory, ClientFactory
from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
fake = Faker()


class ContractorInvoiceFactory(factory.Factory):
    class Meta:
        model = ContractorInvoice

    invoice_number = fake.unique.bothify(text="INV-#####")
    site = factory.SubFactory(SiteFactory)
    invoice_date = fake.date_this_year()
    service_period_start = fake.date_this_year()
    service_period_end = fake.date_this_year()
    gst = fake.boolean()
    amount = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
    status = "PENDING"
    verification_notes = fake.text(max_nb_chars=200)
    verified_by = factory.SubFactory(UserFactory)
    verified_at = fake.date_time_this_year()
    remarks = fake.text(max_nb_chars=200)
    created_by = factory.SubFactory(UserFactory)


class ClientInvoiceFactory(factory.Factory):
    class Meta:
        model = ClientInvoice

    invoice_number = fake.unique.bothify(text="INV-#####")
    site = factory.SubFactory(SiteFactory)
    client = factory.SubFactory(ClientFactory)
    invoice_date = fake.date_this_year()
    service_period_start = fake.date_this_year()
    service_period_end = fake.date_this_year()
    gst = fake.boolean()
    amount = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
    status = "ISSUED"
    remarks = fake.text(max_nb_chars=200)
    created_by = factory.SubFactory(UserFactory)
