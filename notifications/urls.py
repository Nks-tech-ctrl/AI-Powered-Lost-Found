from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list, name='notifications'),
    path('read-all/', views.mark_all_read, name='notifications-read-all'),
    path('<int:pk>/read/', views.mark_as_read, name='notification-read'),
    path('<int:pk>/delete/', views.delete_notification, name='notification-delete'),
]
