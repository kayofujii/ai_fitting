import datetime
import os
import sys
from datetime import timedelta

import cloudinary
import django
from django.utils.timezone import make_aware

sys.path.append('face')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def delete_anonymous_uploaded_image():
    django.setup()
    from face.models import UploadedImage
    one_hour_ago = make_aware(datetime.datetime.now()) - timedelta(hours=1)
    images = UploadedImage.objects.filter(
        author=None, created_at__lte=one_hour_ago).delete()
    for im in images:
        cloudinary.uploader.destroy(im.user_im.public_id)
        cloudinary.uploader.destroy(im.product_im.public_id)
        cloudinary.uploader.destroy(im.image.public_id)
        im.delete()


if __name__ == '__main__':
    delete_anonymous_uploaded_image()
