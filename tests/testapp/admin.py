from django.contrib import admin

from m_django_extensions import S3FileAdminMixin

from .models import Document


@admin.register(Document)
class DocumentAdmin(S3FileAdminMixin, admin.ModelAdmin):
    pass
