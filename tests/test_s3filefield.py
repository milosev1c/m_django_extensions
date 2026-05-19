from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from m_django_extensions.s3filefield import (
    S3FileFormField,
    build_s3_key,
    build_upload_path,
    unique_filename,
)
from tests.testapp.models import Document


@pytest.mark.django_db
def test_build_upload_path_string_upload_to():
    field = Document._meta.get_field("file")
    path = build_upload_path(field, instance=None, filename="report.pdf")
    assert path.endswith("report.pdf")
    assert path.startswith("documents/")


@pytest.mark.django_db
def test_build_upload_path_callable_without_pk():
    field = Document._meta.get_field("callable_file")
    path = build_upload_path(field, instance=Document(title="x"), filename="a.txt")
    assert path == "callable/unsaved/a.txt"


@pytest.mark.django_db
def test_build_upload_path_callable_with_pk():
    doc = Document.objects.create(title="t")
    field = Document._meta.get_field("callable_file")
    path = build_upload_path(field, instance=doc, filename="a.txt")
    assert path == f"callable/{doc.pk}/a.txt"


def test_unique_filename_adds_suffix():
    name = unique_filename("photo.png")
    assert name.endswith(".png")
    assert name.startswith("photo-")
    assert len(name) > len("photo.png")


def test_s3_file_form_field_accepts_path_string():
    field = S3FileFormField(required=False)
    assert field.clean("documents/2026/05/file.pdf") == "documents/2026/05/file.pdf"


def test_s3_file_form_field_empty_clears():
    field = S3FileFormField(required=False)
    assert field.clean("", initial="old/path.pdf") is None


def test_s3_file_form_field_none_keeps_initial():
    field = S3FileFormField(required=False)
    assert field.clean(None, initial="old/path.pdf") == "old/path.pdf"


def test_s3_file_form_field_accepts_uploaded_file():
    field = S3FileFormField(required=True)
    upload = SimpleUploadedFile("x.txt", b"data", content_type="text/plain")
    cleaned = field.clean(upload)
    assert cleaned.name == "x.txt"


def test_build_s3_key_uses_storage_normalize():
    storage = MagicMock()
    storage._normalize_name.side_effect = lambda name: f"normalized/{name}"
    key = build_s3_key(storage, "documents/file.pdf")
    assert key == "normalized/documents/file.pdf"
    storage._normalize_name.assert_called_once()
