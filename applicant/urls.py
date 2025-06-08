# applicant/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()

# Register ViewSets with the router
router.register(r'profiles', views.ApplicantProfileViewSet, basename='profile')
router.register(r'education', views.EducationViewSet, basename='education')
router.register(r'experience', views.WorkExperienceViewSet, basename='experience')
router.register(r'skills', views.SkillViewSet, basename='skills')
router.register(r'projects', views.ProjectViewSet, basename='projects')
router.register(r'certifications', views.CertificationViewSet, basename='certifications')
router.register(r'social-links', views.SocialLinkViewSet, basename='social-links')
router.register(r'job-preferences', views.JobPreferenceViewSet, basename='job-preferences')

# Additional non-ViewSet URLs
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Custom endpoints (non-ViewSet views)
    path('profile/upload-resume/', views.ResumeUploadView.as_view(), name='upload-resume'),
    path('profile/upload-photo/', views.ProfilePhotoUploadView.as_view(), name='upload-photo'),
    path('profile/completion/', views.ProfileCompletionView.as_view(), name='profile-completion'),
    path('locations/', views.LocationListView.as_view(), name='locations'),
    path('industries/', views.IndustryListView.as_view(), name='industries'),
    
    # Dashboard specific endpoints
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/recent-activity/', views.RecentActivityView.as_view(), name='recent-activity'),
]

app_name = 'applicant'