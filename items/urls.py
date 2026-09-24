from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
    path('report-lost/', views.report_lost_view, name='report_lost'),
    path('report-found/', views.report_found_view, name='report_found'),
    path('search/', views.search_view, name='search'),
    path('details/', views.item_details_view, name='item_details'),
    path('<str:id>/', views.item_details_view, name='item_details_id'),
]
