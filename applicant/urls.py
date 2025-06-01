# accounts/urls.py
from django.urls import path
from .views import ApplicantDashboardView

urlpatterns = [
    path('applicant-dashboard/', ApplicantDashboardView.as_view(), name='applicant-dashboard'),
]
