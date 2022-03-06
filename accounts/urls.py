from django.conf.urls import include
from django.urls import path

from .views import SignUpView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('oauth/', include('social_django.urls', namespace='social')),
]
