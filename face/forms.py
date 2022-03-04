from cloudinary.forms import CloudinaryFileField
from django.forms import ModelForm

from .models import UploadedImage


class ImageForm(ModelForm):
    class Meta:
        model = UploadedImage
        fields = ('product_im', 'user_im')
    product_im = CloudinaryFileField(
        options={'folder': 'media/images', })
    user_im = CloudinaryFileField(
        options={'folder': 'media/images', })
