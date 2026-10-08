import pytest
from decouple import config
from django.urls import reverse

from authuser import utils


# ------------------- All Work Complete Tests ------------------ #
def test_all_work_complete_list(api_client, test_complete_work, login_test_admin_user):
    url = reverse('AllWorkCompleteView')
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_all_work_complete_list_unauthorized(api_client, test_complete_work):
    url = reverse('AllWorkCompleteView')
    response = api_client.get(url)
    assert response.status_code == 401

def test_all_work_complete_list_with_contractor(api_client, test_complete_work, login_test_contractor_user):
    url = reverse('AllWorkCompleteView')
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 403


#------------------- Work Complete With ID Tests ------------------ #
def test_get_work_complete_with_id(api_client, test_complete_work, login_test_admin_user):
    url = reverse('WorkCompleteDetailView', args=[test_complete_work.id])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_work_complete_with_invalid_id(api_client, test_complete_work, login_test_admin_user):
    url = reverse('WorkCompleteDetailView', args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 404

def test_get_work_complete_with_id_unauthorized(api_client, test_complete_work):
    url = reverse('WorkCompleteDetailView', args=[test_complete_work.id])
    response = api_client.get(url)
    assert response.status_code == 401