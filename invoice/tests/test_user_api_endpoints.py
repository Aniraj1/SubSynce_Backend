import pytest
from decouple import config
from django.urls import reverse

from authuser import utils



# ------------------- Add Invoice Tests ------------------ #
def test_add_invoice(api_client, test_site, login_test_contractor_user, test_admin_user, login_test_admin_user):
    url = reverse("InvoiceView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "invoice_number": "INV-12345",
        "site": str(test_site.id),
        "invoice_date": "2024-01-01",
        "service_period_start": "2024-01-01",
        "service_period_end": "2024-01-31",
        "amount": 1000.00,
        "remarks": "Test Invoice Remarks"
    }
    response = api_client.post(url, data=payload)
    assert response.status_code == 201

def test_add_invoice_unauthorized(api_client, test_site, login_test_contractor_user):
    url = reverse("InvoiceView")
    payload = {
        "invoice_number": "INV-12345",
        "site": str(test_site.id),
        "invoice_date": "2024-01-01",
        "service_period_start": "2024-01-01",
        "service_period_end": "2024-01-31",
        "amount": 1000.00,
        "remarks": "Test Invoice Remarks"
    }
    response = api_client.post(url, data=payload)
    assert response.status_code == 401

def test_add_invoice_invalid_site_id(api_client, login_test_contractor_user):
    url = reverse("InvoiceView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "invoice_number": "INV-12345",
        "site": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa",
        "invoice_date": "2024-01-01",
        "service_period_start": "2024-01-01",
        "service_period_end": "2024-01-31",
        "amount": 1000.00,
        "remarks": "Test Invoice Remarks"
    }
    response = api_client.post(url, data=payload)
    assert response.status_code == 400

# ------------------- Get Invoice Tests ------------------ #
def test_get_invoice(api_client, test_contractor_invoice, login_test_contractor_user):
    url = reverse("InvoiceView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    print(response.data)
    assert response.status_code == 200

def test_get_invoice_unauthorized(api_client, test_contractor_invoice):
    url = reverse("InvoiceView")
    response = api_client.get(url)
    assert response.status_code == 401


# ------------------- Get Invoice Detail Tests ------------------ #
def test_get_invoice_detail(api_client, test_contractor_invoice, login_test_contractor_user):
    url = reverse("DetailInvoiceView", kwargs={"id": str(test_contractor_invoice.id)})
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_invoice_detail_unauthorized(api_client, test_contractor_invoice):
    url = reverse("DetailInvoiceView", kwargs={"id": str(test_contractor_invoice.id)})
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_invoice_detail_invalid_id(api_client, login_test_contractor_user):
    url = reverse("DetailInvoiceView", kwargs={"id": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa"})
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 404


# ------------------- Update Invoice Tests ------------------ #
def test_update_invoice(api_client, test_contractor_invoice, login_test_contractor_user):
    url = reverse("DetailInvoiceView", kwargs={"id": str(test_contractor_invoice.id)})
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "invoice_number": "INV-54321",
        "site": str(test_contractor_invoice.site.id),
        "invoice_date": "2024-02-01",
        "service_period_start": "2024-02-01",
        "service_period_end": "2024-02-28",
        "amount": 2000.00,
        "remarks": "Updated Invoice Remarksssss"
    }
    response = api_client.put(url, data=payload)
    assert response.status_code == 200

def test_update_invoice_unauthorized(api_client, test_contractor_invoice):
    url = reverse("DetailInvoiceView", kwargs={"id": str(test_contractor_invoice.id)})
    payload = {
        "invoice_number": "INV-54321",
        "site": str(test_contractor_invoice.site.id),
        "invoice_date": "2024-02-01",
        "service_period_start": "2024-02-01",
        "service_period_end": "2024-02-28",
        "amount": 2000.00,
        "remarks": "Updated Invoice Remarks"
    }
    response = api_client.put(url, data=payload)
    assert response.status_code == 401

def test_update_invoice_invalid_invoice_id(api_client, test_contractor_invoice, login_test_contractor_user):
    url = reverse("DetailInvoiceView", kwargs={"id": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa"})
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "invoice_number": "INV-54321",
        "site": str(test_contractor_invoice.site.id),
        "invoice_date": "2024-02-01",
        "service_period_start": "2024-02-01",
        "service_period_end": "2024-02-28",
        "amount": 2000.00,
        "remarks": "Updated Invoice Remarks"
    }
    response = api_client.put(url, data=payload)
    assert response.status_code == 404


# ------------------- Delete Invoice Tests ------------------ #
def test_delete_invoice(api_client, test_contractor_invoice, login_test_contractor_user):
    url = reverse("DetailInvoiceView", kwargs={"id": str(test_contractor_invoice.id)})
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.delete(url)
    assert response.status_code == 200

def test_delete_invoice_unauthorized(api_client, test_contractor_invoice):
    url = reverse("DetailInvoiceView", kwargs={"id": str(test_contractor_invoice.id)})
    response = api_client.delete(url)
    assert response.status_code == 401

def test_delete_invoice_invalid_invoice_id(api_client, test_contractor_invoice, login_test_contractor_user):
    url = reverse("DetailInvoiceView", kwargs={"id": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa"})
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.delete(url)
    assert response.status_code == 404


# ------------------- Get Total Earnings Tests ------------------ #
def test_get_total_earnings(api_client, test_contractor_invoice, login_test_contractor_user):
    test_contractor_invoice.status = "APPROVED"
    test_contractor_invoice.save(update_fields=["status"])
    url = reverse("TotalEarningsView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_total_earnings_unauthorized(api_client, test_contractor_invoice):
    url = reverse("TotalEarningsView")
    response = api_client.get(url)
    assert response.status_code == 401
