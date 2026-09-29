from django.urls import path
from . import views

urlpatterns = [
    # Claimant views
    path('', views.my_claims, name='my-claims'),
    path('item/<int:pk>/submit/', views.submit_claim, name='submit-claim'),
    path('<int:pk>/cancel/', views.cancel_claim, name='cancel-claim'),

    # Reporter review views
    path('review/', views.claims_to_review, name='claims-to-review'),
    path('review/<int:pk>/', views.review_claim, name='review-claim'),
    path('<int:pk>/approve/', views.approve_claim, name='approve-claim'),
    path('<int:pk>/reject/', views.reject_claim, name='reject-claim'),

    # Backwards-compatibility aliases
    path('my/', views.my_claims, name='claims'),
]
