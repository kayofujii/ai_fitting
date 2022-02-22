from django.urls import path

from . import views

urlpatterns = [
    # path('', views.home, name='home'),
    path("", views.index, name="index"),
    path("upload", views.upload_image, name="upload"),
]
