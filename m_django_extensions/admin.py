from __future__ import annotations

from django.urls import path

from .views import make_s3_presign_view


class S3FileAdminMixin:
    """
    Add presigned-upload endpoint for S3FileField widgets on this ModelAdmin.

    Inherit before admin.ModelAdmin::

        class ArticleAdmin(S3FileAdminMixin, admin.ModelAdmin):
            ...
    """

    def get_urls(self):
        urls = super().get_urls()
        opts = self.model._meta
        custom = [
            path(
                "s3-presign/",
                self.admin_site.admin_view(make_s3_presign_view(self)),
                name=f"{opts.app_label}_{opts.model_name}_s3_presign",
            ),
        ]
        return custom + urls

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        from .s3filefield import S3FileField

        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, S3FileField):
            opts = self.model._meta
            presign_url = self._reverse_presign_url(opts)
            widget = formfield.widget
            widget.presign_url = presign_url
            widget.app_label = opts.app_label
            widget.model_name = opts.model_name
            widget.field_name = db_field.name
            if request.resolver_match:
                widget.object_id = request.resolver_match.kwargs.get("object_id", "")
            else:
                widget.object_id = ""
        return formfield

    def _reverse_presign_url(self, opts):
        from django.urls import reverse

        return reverse(
            f"admin:{opts.app_label}_{opts.model_name}_s3_presign",
            current_app=self.admin_site.name,
        )
