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
    path('', views.search_view, name='browse-items'),

    # Item Detail, Edit, and Delete routes (Owner only)
    path('<int:pk>/', views.item_detail, name='item-detail'),
    path('<int:pk>/edit/', views.item_edit, name='item-edit'),
    path('<int:pk>/delete/', views.item_delete, name='item-delete'),

    # Public Item Detail routes
    path('view/<int:pk>/', views.public_item_detail, name='public-item-detail'),
    path('public/<int:pk>/', views.public_item_detail, name='public-item-detail-alt'),
    path('<int:pk>/public/', views.public_item_detail, name='public-item-detail-legacy'),

    # Compatibility aliases
    path('<int:id>/detail/', views.item_detail, name='item_details_id'),
    path('details/', views.my_reports, name='item_details'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
]

