from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('users/', views.users_list, name='users-list'),
    path('users/<int:pk>/', views.user_detail, name='user-detail'),
    path('items/', views.items_list, name='items-list'),
    path('items/<int:pk>/', views.item_detail, name='item-detail'),
    path('moderation/', views.moderation_queue, name='moderation-queue'),
    path('claims/', views.claims_list, name='claims-list'),
    path('claims/<int:pk>/', views.claim_detail, name='claim-detail'),
    path('notifications/', views.notifications_overview, name='notifications-list'),
    path('email-deliveries/', views.email_deliveries_list, name='email-deliveries-list'),
    path('audit-logs/', views.audit_logs_list, name='audit-logs-list'),
    path('settings/', views.settings_view, name='settings'),
    path('api/poll-updates/', views.poll_updates_api, name='poll-updates'),
]
