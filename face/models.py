import hashlib
import os.path

from django.contrib.auth.models import User
from django.db import models


def get_image_path(instance, filename):
    return "face_images/%s%s" % (
        hashlib.sha1(
            (str(instance.created_at) + filename).encode("utf-8")).hexdigest(),
        os.path.splitext(filename)[1],
    )


class UploadedImage(models.Model):
    user_im = models.ImageField(
        upload_to=get_image_path, null=True, blank=True)
    product_im = models.ImageField(
        upload_to=get_image_path, null=True, blank=True)
    image = models.ImageField(upload_to=get_image_path, null=True, blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
