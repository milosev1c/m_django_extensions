# m-django-extensions

Django field extensions and admin widgets.

## WebPImageField

`WebPImageField` converts uploaded images to WebP on save.

## S3FileField

`S3FileField` is a `FileField` for S3-compatible storage with **direct browser upload** via presigned POST in the Django admin. Files can be uploaded before the parent object is saved (add form).

### Install

```bash
pip install m-django-extensions[s3]
```

Add the app so templates and static files are discovered:

```python
INSTALLED_APPS = [
    # ...
    "m_django_extensions",
]
```

Configure S3 storage (example with django-storages):

```python
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": "my-bucket",
            # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_ENDPOINT_URL, etc.
        },
    },
}
```

### Model and admin

```python
from m_django_extensions import S3FileField, S3FileAdminMixin

class Article(models.Model):
    attachment = S3FileField(upload_to="articles/%Y/%m/")

@admin.register(Article)
class ArticleAdmin(S3FileAdminMixin, admin.ModelAdmin):
    pass
```

Each `ModelAdmin` that uses `S3FileField` must inherit `S3FileAdminMixin` (before `admin.ModelAdmin`).

### How it works

1. Staff selects a file in the admin widget.
2. JavaScript requests a presigned POST from `…/admin/…/<model>/s3-presign/`.
3. The server builds the object key from the field’s `upload_to` and returns presigned POST data plus the storage-relative `path`.
4. The browser uploads directly to S3 with a progress bar.
5. The widget stores `path` in a hidden input; saving the model persists that path without re-uploading.

### upload_to on add forms

On the add form there is no saved instance yet. Use `upload_to` paths that do not require a primary key (e.g. `"articles/%Y/%m/"` or a callable that only needs `filename`).

### CORS

The bucket must allow `POST` from your admin origin, for example:

```xml
<CORSRule>
  <AllowedOrigin>https://your-admin-host.example</AllowedOrigin>
  <AllowedMethod>POST</AllowedMethod>
  <AllowedHeader>*</AllowedHeader>
</CORSRule>
```

### Options

- `max_upload_bytes` on `S3FileField` (default 100 MiB) — enforced in presigned POST conditions.
