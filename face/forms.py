from cloudinary.forms import CloudinaryFileField
from django import forms


class ImageForm(forms.Form):
    product_im = forms.ImageField()
    user_im = forms.ImageField()
