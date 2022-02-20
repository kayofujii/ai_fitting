from django.urls import path

from . import views

urlpatterns = [
    path("", views.upload_image, name="index"),
    path("upload", views.upload_image, name="upload"),
]
