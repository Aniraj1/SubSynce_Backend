import pytest
from decouple import config
from django.urls import reverse

from authuser import utils

# ------------------- Verify Invoice Tests ------------------ #
def test_verify_invoice(api_client, test_contractor_invoice, login_test_admin_user):
    url = reverse("InvoiceVerificationView", args=[str(test_contractor_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "status": "APPROVED",
        "verification_notes": "Invoice verified successfully."
    }

    response = api_client.patch(url, payload)
    assert response.status_code == 200

def test_verify_invoice_unauthorized(api_client, test_contractor_invoice, login_test_contractor_user):
    url = reverse("InvoiceVerificationView", args=[str(test_contractor_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "status": "APPROVED",
        "verification_notes": "Invoice verified successfully."
    }

    response = api_client.patch(url, payload)
    assert response.status_code == 403

def test_verify_invoice_invalid_status(api_client, test_contractor_invoice, login_test_admin_user):
    url = reverse("InvoiceVerificationView", args=[str(test_contractor_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "status": "INVALID_STATUS",
        "verification_notes": "Invoice verified successfully."
    }

    response = api_client.patch(url, payload)
    assert response.status_code == 400

def test_verify_invoice_invalid_id(api_client, login_test_admin_user):
    url = reverse("InvoiceVerificationView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "status": "APPROVED",
        "verification_notes": "Invoice verified successfully."
    }

    response = api_client.patch(url, payload)
    assert response.status_code == 404


# ------------------- Get Invoice Tests ------------------ #
def test_get_invoice(api_client, test_contractor_invoice, login_test_admin_user):
    url = reverse("AllInvoiceAdminView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_invoice_unauthorized(api_client, test_contractor_invoice):
    url = reverse("AllInvoiceAdminView")
    response = api_client.get(url)
    assert response.status_code == 401


# ------------------- Get Invoice Detail Tests ------------------ #
def test_get_invoice_detail(api_client, test_contractor_invoice, login_test_admin_user):
    url = reverse("GetDetailInvoiceAdminView", args=[str(test_contractor_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_invoice_detail_unauthorized(api_client, test_contractor_invoice):
    url = reverse("GetDetailInvoiceAdminView", args=[str(test_contractor_invoice.id)])
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_invoice_detail_invalid_id(api_client, login_test_admin_user):
    url = reverse("GetDetailInvoiceAdminView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 404



# ------------------- Expenditure Tests ------------------ #
def test_get_expenditure(api_client, test_contractor_invoice, login_test_admin_user):
    url = reverse("TotalExpenditureAdminView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_expenditure_unauthorized(api_client, test_contractor_invoice):
    url = reverse("TotalExpenditureAdminView")
    response = api_client.get(url)
    assert response.status_code == 401


# ------------------- Add Client Invoice Tests ------------------ #
def test_add_client_invoice(api_client, test_site, login_test_admin_user):
    url = reverse("ClientInvoiceViews")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "site": str(test_site.id),
        "client": str(test_site.client_id.id),
        "invoice_number": "INV-001",
        "invoice_date": "2023-08-01",
        "service_period_start": "2023-07-01",
        "service_period_end": "2023-07-31",
        "amount": 1000.00,
        "remarks": "Test client invoice"
    }
    response = api_client.post(url, payload)
    assert response.status_code == 201

def test_add_client_invoice_unauthorized(api_client, test_site):
    url = reverse("ClientInvoiceViews")
    payload = {
        "site": str(test_site.id),
        "client": str(test_site.client_id.id),
        "invoice_number": "INV-001",
        "invoice_date": "2023-08-01",
        "service_period_start": "2023-07-01",
        "service_period_end": "2023-07-31",
        "amount": 1000.00,
        "remarks": "Test client invoice"
    }
    response = api_client.post(url, payload)
    assert response.status_code == 401

def test_add_client_invoice_invalid_data(api_client, test_site, login_test_admin_user):
    url = reverse("ClientInvoiceViews")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "site": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa",
        "client": str(test_site.client_id.id),
        "invoice_number": "INV-001",
        "invoice_date": "2023-08-01",
        "service_period_start": "2023-07-01",
        "service_period_end": "2023-07-31",
        "amount": 1000.00,
        "remarks": "Test client invoice"
    }
    response = api_client.post(url, payload)
    assert response.status_code == 400


# ------------------- Get Client Invoice Tests ------------------ #
def test_get_client_invoice(api_client, test_client_invoice, login_test_admin_user):
    url = reverse("ClientInvoiceViews")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    print(response.data)
    assert response.status_code == 200

def test_get_client_invoice_unauthorized(api_client, test_client_invoice):
    url = reverse("ClientInvoiceViews")
    response = api_client.get(url)
    assert response.status_code == 401


# ------------------- Get Client Invoice Detail Tests ------------------ #
def test_get_client_invoice_detail(api_client, test_client_invoice, login_test_admin_user):
    url = reverse("DetailClientInvoiceView", args=[str(test_client_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_client_invoice_detail_unauthorized(api_client, test_client_invoice):
    url = reverse("DetailClientInvoiceView", args=[str(test_client_invoice.id)])
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_client_invoice_detail_invalid_id(api_client, login_test_admin_user):
    url = reverse("DetailClientInvoiceView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 404



# ------------------- Update Client Invoice Tests ------------------ #
def test_update_client_invoice(api_client, test_site, test_client_invoice, login_test_admin_user):
    url = reverse("DetailClientInvoiceView", args=[str(test_client_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "invoice_number": "string",
        "invoice_date": "2026-10-08",
        "site": str(test_site.id),
        "client": str(test_site.client_id.id),
        "service_period_start": "2026-10-08",
        "service_period_end": "2026-10-08",
        "amount": "9009",
        "remarks": "Invoice remarks",
    }
    response = api_client.put(url, payload)
    assert response.status_code == 200

def test_update_client_invoice_unauthorized(api_client, test_site, test_client_invoice):
    url = reverse("DetailClientInvoiceView", args=[str(test_client_invoice.id)])
    payload = {
        "invoice_number": "string",
        "invoice_date": "2026-10-08",
        "site": str(test_site.id),
        "client": str(test_site.client_id.id),
        "service_period_start": "2026-10-08",
        "service_period_end": "2026-10-08",
        "amount": "9009",
        "remarks": "Invoice remarks",
    }
    response = api_client.put(url, payload)
    assert response.status_code == 401

def test_update_client_invoice_invalid_id(api_client, test_site, login_test_admin_user):
    url = reverse("DetailClientInvoiceView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "invoice_number": "string",
        "invoice_date": "2026-10-08",
        "site": str(test_site.id),
        "client": str(test_site.client_id.id),
        "service_period_start": "2026-10-08",
        "service_period_end": "2026-10-08",
        "amount": "9009",
        "remarks": "Invoice remarks",
    }
    response = api_client.put(url, payload)
    assert response.status_code == 404

def test_update_client_invoice_invalid_data(api_client, test_site, test_client_invoice, login_test_admin_user):
    url = reverse("DetailClientInvoiceView", args=[str(test_client_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "invoice_number": "string",
        "invoice_date": "2026-10-08",
        "site": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa",
        "client": str(test_site.client_id.id),
        "service_period_start": "2026-10-08",
        "service_period_end": "2026-10-08",
        "amount": "9009",
        "remarks": "Invoice remarks",
    }
    response = api_client.put(url, payload)
    assert response.status_code == 400


# ------------------- Update Client Invoice Status Tests ------------------ #
def test_update_client_invoice_status(api_client, test_client_invoice, login_test_admin_user):
    url = reverse("ClientInvoiceStatusUpdateView", args=[str(test_client_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "status": "PAID"
    }
    response = api_client.put(url, payload)
    assert response.status_code == 200

def test_update_client_invoice_status_unauthorized(api_client, test_client_invoice):
    url = reverse("ClientInvoiceStatusUpdateView", args=[str(test_client_invoice.id)])
    payload = {
        "status": "PAID"
    }
    response = api_client.put(url, payload)
    assert response.status_code == 401

def test_update_client_invoice_status_invalid_id(api_client, login_test_admin_user):
    url = reverse("ClientInvoiceStatusUpdateView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    payload = {
        "status": "PAID"
    }
    response = api_client.put(url, payload)
    assert response.status_code == 404



# ------------------- Delete Client Invoice Tests ------------------ #
def test_delete_client_invoice(api_client, test_client_invoice, login_test_admin_user):
    url = reverse("DetailClientInvoiceView", args=[str(test_client_invoice.id)])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.delete(url)
    assert response.status_code == 204

def test_delete_client_invoice_unauthorized(api_client, test_client_invoice):
    url = reverse("DetailClientInvoiceView", args=[str(test_client_invoice.id)])
    response = api_client.delete(url)
    assert response.status_code == 401

def test_delete_client_invoice_invalid_id(api_client, login_test_admin_user):
    url = reverse("DetailClientInvoiceView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.delete(url)
    assert response.status_code == 404
    

# ------------------- Revenue Report Tests ------------------ #
def test_get_revenue_report(api_client, test_client_invoice, login_test_admin_user):
    test_client_invoice.status = "PAID"
    test_client_invoice.save()
    url = reverse("RevenueReportView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    print(response.data)
    assert response.status_code == 200

def test_get_revenue_report_unauthorized(api_client, test_client_invoice):
    url = reverse("RevenueReportView")
    response = api_client.get(url)
    assert response.status_code == 401