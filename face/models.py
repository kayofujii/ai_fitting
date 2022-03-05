from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.db import models


class UploadedImage(models.Model):
    user_im = CloudinaryField(
        'image', blank=True, null=True, folder="media/face_images")
    product_im = CloudinaryField(
        'image', blank=True, null=True, folder="media/face_images")
    image = CloudinaryField('image', blank=True, null=True,
                            folder="media/face_images")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=256, null=True, blank=True)
