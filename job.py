import os
import sys

import django

sys.path.append('face')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def delete_anonymous_uploaded_image():
    django.setup()
    from face.models import UploadedImage

    UploadedImage.objects.filter(author=None).delete()


if __name__ == '__main__':
    delete_anonymous_uploaded_image()
