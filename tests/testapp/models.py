from django.db import models

from m_django_extensions import S3FileField


def upload_to_callable(instance, filename):
    prefix = str(instance.pk) if instance and instance.pk else "unsaved"
    return f"callable/{prefix}/{filename}"


class Document(models.Model):
    title = models.CharField(max_length=100)
    file = S3FileField(upload_to="documents/%Y/%m/")
    callable_file = S3FileField(upload_to=upload_to_callable)
