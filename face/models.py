import hashlib
import os.path

from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.db import models


def get_image_path(instance, filename):
    return "face_images/%s%s" % (
        hashlib.sha1(
            (str(instance.created_at) + filename).encode("utf-8")).hexdigest(),
        os.path.splitext(filename)[1],
    )


class UploadedImage(models.Model):
    user_im = CloudinaryField('image', blank=True, null=True,)
    product_im = CloudinaryField('image', blank=True, null=True,)
    image = CloudinaryField('image', blank=True, null=True,
                            folder="media/face_images")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=256, null=True, blank=True)
