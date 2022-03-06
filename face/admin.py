from django.contrib import admin

from .models import Order, UploadedImage

admin.site.register(UploadedImage)
admin.site.register(Order)
