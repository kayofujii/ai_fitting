from cloudinary.forms import CloudinaryFileField
from django import forms


class ImageForm(forms.Form):
    product_im = CloudinaryFileField(options={
        'folder': 'media/face_images', })
    user_im = CloudinaryFileField(options={
        'folder': 'media/face_images',
    })
