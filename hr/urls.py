# hr/urls.py

from django.urls import path
from .views import HRDashboardView

urlpatterns = [
    path('dashboard/', HRDashboardView.as_view(), name='hr-dashboard'),
]
