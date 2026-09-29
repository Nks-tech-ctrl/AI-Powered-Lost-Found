from django.urls import path
from . import views

urlpatterns = [
    # Static action and listing routes (must precede <int:pk>/)
    path('report-lost/', views.report_lost, name='report-lost'),
    path('report-found/', views.report_found, name='report-found'),
    # Backwards-compatible aliases
    path('report_lost/', views.report_lost, name='report_lost'),
    path('report_found/', views.report_found, name='report_found'),
    path('my-reports/', views.my_reports, name='my-reports'),
    path('search/', views.search_view, name='search'),

    # Item Detail, Edit, and Delete routes
    path('<int:pk>/', views.item_detail, name='item-detail'),
    path('<int:pk>/edit/', views.item_edit, name='item-edit'),
    path('<int:pk>/delete/', views.item_delete, name='item-delete'),

    # Compatibility aliases
    path('<int:id>/detail/', views.item_detail, name='item_details_id'),
    path('details/', views.my_reports, name='item_details'),
    path('', views.dashboard_view, name='items_dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
]

