
import os
import sys
from datetime import date, datetime

import cloudinary
import django
from dateutil.relativedelta import relativedelta
from django.utils.timezone import make_aware

sys.path.append('face')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def delete_anonymous_uploaded_image():
    django.setup()
    from face.models import UploadedImage
    one_month_ago = make_aware(
        datetime.now()) - relativedelta(months=1)
    images = UploadedImage.objects.filter(
        is_deleted=True, created_at__lte=one_month_ago)
    for im in images:
        cloudinary.uploader.destroy(im.user_im.public_id)
        cloudinary.uploader.destroy(im.product_im.public_id)
        cloudinary.uploader.destroy(im.image.public_id)
        im.delete()


if __name__ == '__main__':
    delete_anonymous_uploaded_image()
