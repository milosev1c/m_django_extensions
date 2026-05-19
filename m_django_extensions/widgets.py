from __future__ import annotations

from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class S3FileAdminWidget(forms.Widget):
    """Admin widget: presigned direct upload to S3 with progress bar."""

    template_name = "m_django_extensions/widgets/s3filewidget.html"

    presign_url: str = ""
    app_label: str = ""
    model_name: str = ""
    field_name: str = ""
    object_id: str = ""

    class Media:
        css = {
            "all": ("m_django_extensions/css/s3filewidget.css",),
        }
        js = ("m_django_extensions/js/s3filewidget.js",)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget_attrs = context["widget"]["attrs"]
        widget_attrs.setdefault("class", "")
        widget_attrs["class"] = f"{widget_attrs['class']} s3-file-widget".strip()
        widget_attrs["data-presign-url"] = self.presign_url
        widget_attrs["data-app-label"] = self.app_label
        widget_attrs["data-model-name"] = self.model_name
        widget_attrs["data-field-name"] = self.field_name
        widget_attrs["data-object-id"] = self.object_id or ""
        context["current_value"] = value or ""
        context["display_name"] = value.split("/")[-1] if value else ""
        return context

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        return mark_safe(render_to_string(self.template_name, context))

    def value_from_datadict(self, data, files, name):
        return data.get(name)
