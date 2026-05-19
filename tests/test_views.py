from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from tests.testapp.models import Document


def _presign_post_data(**overrides):
    data = {
        "app_label": "testapp",
        "model_name": "document",
        "field_name": "file",
        "filename": "report.pdf",
    }
    data.update(overrides)
    return data


@pytest.fixture
def staff_client(db):
    user = User.objects.create_superuser("admin", "admin@test.com", "password")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def mock_s3_storage():
    client = MagicMock()
    connection = MagicMock()
    connection.meta.client = client
    client.generate_presigned_post.return_value = {
        "url": "https://bucket.s3.amazonaws.com/",
        "fields": {"key": "documents/2026/05/file-abc.pdf", "policy": "x"},
    }

    storage = MagicMock()
    storage.bucket_name = "test-bucket"
    storage.connection = connection
    storage._normalize_name.side_effect = lambda name: name.lstrip("/")

    return storage, client


@pytest.mark.django_db
def test_s3_presign_view_returns_presigned_post(staff_client, mock_s3_storage):
    storage, boto_client = mock_s3_storage
    field = Document._meta.get_field("file")

    with patch.object(field, "storage", storage):
        url = reverse("admin:testapp_document_s3_presign")
        response = staff_client.post(
            url,
            _presign_post_data(content_type="application/pdf"),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://bucket.s3.amazonaws.com/"
    assert "fields" in data
    assert data["path"].endswith(".pdf")
    assert data["path"].startswith("documents/")
    boto_client.generate_presigned_post.assert_called_once()


@pytest.mark.django_db
def test_s3_presign_view_rejects_non_s3_field(staff_client):
    url = reverse("admin:testapp_document_s3_presign")
    response = staff_client.post(url, _presign_post_data(field_name="title"))
    assert response.status_code == 400
    assert "not an S3FileField" in response.json()["error"]


@pytest.mark.django_db
def test_s3_presign_view_requires_staff(db):
    url = reverse("admin:testapp_document_s3_presign")
    client = Client()
    response = client.post(url, _presign_post_data())
    assert response.status_code in (302, 403)


@pytest.fixture
def add_only_client(db):
    user = User.objects.create_user("adder", password="password", is_staff=True)
    content_type = ContentType.objects.get_for_model(Document)
    add_permission = Permission.objects.get(
        codename="add_document",
        content_type=content_type,
    )
    user.user_permissions.add(add_permission)
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_s3_presign_add_form_allows_add_permission_only(add_only_client, mock_s3_storage):
    storage, boto_client = mock_s3_storage
    field = Document._meta.get_field("file")

    with patch.object(field, "storage", storage):
        url = reverse("admin:testapp_document_s3_presign")
        response = add_only_client.post(url, _presign_post_data())

    assert response.status_code == 200
    boto_client.generate_presigned_post.assert_called_once()


@pytest.mark.django_db
def test_s3_presign_change_form_denied_without_change_permission(add_only_client, mock_s3_storage):
    doc = Document.objects.create(title="t")
    storage, _ = mock_s3_storage
    field = Document._meta.get_field("file")

    with patch.object(field, "storage", storage):
        url = reverse("admin:testapp_document_s3_presign")
        response = add_only_client.post(url, _presign_post_data(object_id=str(doc.pk)))

    assert response.status_code == 403
