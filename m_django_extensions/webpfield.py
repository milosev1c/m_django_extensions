from io import BytesIO
from pathlib import PurePosixPath

from PIL import Image, ImageFile
from django.core.files.base import ContentFile
from django.db.models import ImageField

ImageFile.LOAD_TRUNCATED_IMAGES = True


class WebPImageField(ImageField):
    """
    ImageField that converts uploaded images to WebP on save.

    :param webp_quality: WebP quality (default 80).
    :param webp_lossless: Force lossless encoding (default False).
        Also enabled automatically for RGBA images.
    :param webp_method: WebP encoding method 0–6 (default 4).
    """

    def __init__(self, verbose_name=None, name=None, width_field=None, height_field=None, **kwargs):
        self.webp_quality = kwargs.pop("webp_quality", 80)
        self.webp_lossless = kwargs.pop("webp_lossless", False)
        self.webp_method = kwargs.pop("webp_method", 4)
        super().__init__(verbose_name, name, width_field, height_field, **kwargs)

    def save_form_data(self, instance, data):
        if not data:
            super().save_form_data(instance, data)
            return

        path = PurePosixPath(data.name)
        if path.suffix.lower() == ".webp":
            super().save_form_data(instance, data)
            return

        data.seek(0)
        with Image.open(data) as image:
            lossless = self.webp_lossless or image.mode == "RGBA"
            save_kwargs = {
                "format": "WEBP",
                "lossless": lossless,
                "method": self.webp_method,
            }
            if not lossless:
                save_kwargs["quality"] = self.webp_quality

            with BytesIO() as buffer:
                image.save(buffer, **save_kwargs)
                data = ContentFile(buffer.getvalue(), name=f"{path.stem}.webp")

        super().save_form_data(instance, data)
