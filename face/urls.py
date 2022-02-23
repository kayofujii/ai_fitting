from django.urls import path

from . import views

urlpatterns = [
    # path('', views.home, name='home'),
    path("", views.index, name="index"),
    path("help", views.help, name="help"),
    path("upload", views.upload_image, name="upload"),
]
