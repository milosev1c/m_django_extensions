from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile
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
        if data is None:
            return
        if not data.name.endswith(".webp"):  # convert only non-webp files
            image = Image.open(data)
            filename_list = data.name.split(".")
            filename = f"{'.'.join(filename_list[:-1])}.webp"
            with BytesIO() as buffer:
                image.save(buffer, 'webp')
                data = ContentFile(buffer.getvalue(), name=filename)
        super().save_form_data(instance, data)
