from __future__ import annotations

import os
import uuid
from pathlib import PurePosixPath

from django import forms
from django.db import models
from django.utils.text import get_valid_filename

DEFAULT_MAX_UPLOAD_BYTES = 100 * 1024 * 1024


def build_upload_path(field: models.FileField, *, instance, filename: str) -> str:
    """Resolve storage-relative path using the field's upload_to."""
    upload_to = field.upload_to
    safe_name = get_valid_filename(filename)
    if callable(upload_to):
        return upload_to(instance, safe_name)
    return os.path.join(upload_to, safe_name).replace("\\", "/")


def unique_filename(filename: str) -> str:
    """Prefix filename with UUID to reduce collisions on add forms."""
    path = PurePosixPath(get_valid_filename(filename))
    stem = path.stem or "file"
    suffix = path.suffix
    return f"{stem}-{uuid.uuid4().hex[:8]}{suffix}"


def build_s3_key(storage, relative_path: str) -> str:
    """Build the full S3 object key from a storage-relative path."""
    normalized = storage._normalize_name(relative_path.lstrip("/"))
    return normalized.replace("\\", "/")


class S3FileFormField(forms.FileField):
    """Accepts a storage path string from presigned upload or a normal UploadedFile."""

    def clean(self, data, initial=None):
        if data is None:
            return initial

        if data == "":
            if self.required:
                raise forms.ValidationError(self.error_messages["required"], code="required")
            return None

        if isinstance(data, str):
            return data

        return super().clean(data, initial)


class S3FileField(models.FileField):
    """
    FileField for S3-compatible storage with admin presigned direct upload.

    Use with S3FileAdminMixin on the model's ModelAdmin.
    """

    def __init__(self, *args, max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES, **kwargs):
        self.max_upload_bytes = max_upload_bytes
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        from .widgets import S3FileAdminWidget

        kwargs.setdefault("form_class", S3FileFormField)
        kwargs.setdefault("widget", S3FileAdminWidget)
        return super().formfield(**kwargs)

    def save_form_data(self, instance, data):
        if isinstance(data, str):
            setattr(instance, self.attname, data)
            return
        super().save_form_data(instance, data)
