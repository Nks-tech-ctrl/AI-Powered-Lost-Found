from django.urls import path
from . import views

urlpatterns = [
    path('', views.matches_view, name='matches'),
]
