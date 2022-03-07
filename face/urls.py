from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("fitting", views.fitting, name="fitting"),
    path("detail/<str:token>", views.detail, name="detail"),
    path("logical_delete_image/<int:im_id>", views.logical_delete_image,
         name="logical_delete_image"),
    path("physical_delete_image/<int:im_id>", views.physical_delete_image,
         name="physical_delete_image"),
    path("user_info", views.user_info, name="user_info"),
    path("help", views.help, name="help"),
    path("about", views.about, name="about"),
    path("upload", views.upload_image, name="upload"),
    path('create_checkout_session', views.create_checkout_session,
         name='create_checkout_session'),
    path('stop_subscription_session', views.stop_subscription_session,
         name='stop_subscription_session'),
    path('checkout/success', views.checkout_success, name='checkout_success'),
    path('stop/success', views.stop_success, name='stop_success'),
    path('webhook', views.checkout_success_webhook,
         name='checkout_success_webhook'),
]
