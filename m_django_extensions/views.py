from __future__ import annotations

from django.apps import apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from .s3filefield import S3FileField, build_s3_key, build_upload_path, unique_filename


def _get_s3_field(model, field_name: str) -> S3FileField:
    try:
        field = model._meta.get_field(field_name)
    except Exception as exc:
        raise ValidationError(f"Unknown field: {field_name}") from exc

    if not isinstance(field, S3FileField):
        raise ValidationError(f"Field {field_name} is not an S3FileField")

    return field


def _get_storage_client(storage):
    if not hasattr(storage, "bucket_name"):
        raise ValidationError("Field storage is not S3-compatible (missing bucket_name)")

    connection = getattr(storage, "connection", None)
    if connection is None:
        raise ValidationError("Field storage has no S3 connection")

    return connection.meta.client, storage.bucket_name


def _generate_presigned_post(
    *,
    storage,
    relative_path: str,
    content_type: str | None,
    max_upload_bytes: int,
):
    client, bucket = _get_storage_client(storage)
    key = build_s3_key(storage, relative_path)

    conditions: list = [
        ["content-length-range", 1, max_upload_bytes],
    ]
    fields: dict = {}

    if content_type:
        fields["Content-Type"] = content_type
        conditions.append({"Content-Type": content_type})

    post = client.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields=fields or None,
        Conditions=conditions,
        ExpiresIn=900,
    )
    return post, relative_path


def _check_presign_permission(request: HttpRequest, model_admin, object_id: str | None) -> None:
    """Add forms need add permission; change forms need change permission."""
    if object_id:
        if not model_admin.has_change_permission(request):
            raise PermissionDenied
    elif not model_admin.has_add_permission(request):
        raise PermissionDenied


def s3_presign_view(request: HttpRequest, model_admin) -> JsonResponse:
    """Generate a presigned POST for direct browser upload to S3."""
    app_label = request.POST.get("app_label", "")
    model_name = request.POST.get("model_name", "")
    field_name = request.POST.get("field_name", "")
    filename = request.POST.get("filename", "")
    content_type = request.POST.get("content_type") or None
    object_id = request.POST.get("object_id") or None

    _check_presign_permission(request, model_admin, object_id)

    if not all([app_label, model_name, field_name, filename]):
        return JsonResponse({"error": "Missing required parameters."}, status=400)

    model = apps.get_model(app_label, model_name)
    if model_admin.model is not model:
        return JsonResponse({"error": "Model mismatch."}, status=400)

    try:
        field = _get_s3_field(model, field_name)
    except ValidationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    instance = None
    if object_id:
        instance = model_admin.get_queryset(request).filter(pk=object_id).first()

    unique_name = unique_filename(filename)
    relative_path = build_upload_path(field, instance=instance, filename=unique_name)

    try:
        post, path = _generate_presigned_post(
            storage=field.storage,
            relative_path=relative_path,
            content_type=content_type,
            max_upload_bytes=field.max_upload_bytes,
        )
    except ValidationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"error": f"Presign failed: {exc}"}, status=500)

    return JsonResponse(
        {
            "url": post["url"],
            "fields": post["fields"],
            "path": path,
        }
    )


def make_s3_presign_view(model_admin):
    """Return a view callable bound to model_admin for URL registration."""

    @require_POST
    def view(request: HttpRequest):
        return s3_presign_view(request, model_admin)

    return view
