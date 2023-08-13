from io import BytesIO

from PIL import Image
from django.db.models import ImageField


class WebPImageField(ImageField):
    """
    This is a field to automatically convert images to Webp format
    Usage: replace ImageField with this one. No migrations needed.
    :param webp_quality - WebP quality (80)
    :param webp_lossless - loseless enabled? (false)
    :param webp_method -
    """
    def __init__(self, verbose_name=None, name=None, width_field=None, height_field=None, **kwargs):
        self.webp_quality = kwargs.pop('webp_quality', 80)
        self.webp_lossless = kwargs.pop('webp_lossless', False)
        self.webp_method = kwargs.pop('webp_method', 4)
        super(WebPImageField, self).__init__(verbose_name, name, width_field, height_field, **kwargs)

    def save_form_data(self, instance, data):
        if data and data.name:
            image = Image.open(data)
            image = image.convert("RGB")

            webp_image_name = f"{data.name.rsplit('.', 1)[0]}.webp"
            webp_image_bytes = BytesIO()
            image.save(
                webp_image_bytes,
                "WEBP",
                quality=self.webp_quality,
                lossless=self.webp_lossless,
                method=self.webp_method
            )
            webp_image_bytes.seek(0)

            data.file = webp_image_bytes
            data.name = webp_image_name

        super().save_form_data(instance, data)
