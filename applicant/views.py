# applicant/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import (
    ApplicantProfile, Location, Education, WorkExperience, 
    Skill, Project, Certification, JobPreference, Industry, SocialLink
)
from .serializers import (
    ApplicantProfileSerializer, CompleteProfileSerializer, ProfileSummarySerializer,
    EducationSerializer, WorkExperienceSerializer, SkillSerializer, BulkSkillsSerializer,
    ProjectSerializer, CertificationSerializer, SocialLinkSerializer,
    JobPreferenceSerializer, LocationSerializer, IndustrySerializer
)


class ApplicantProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing applicant profiles
    Endpoints:
    - GET /api/v1/profiles/ - List all profiles (admin only)
    - GET /api/v1/profiles/my_profile/ - Get current user's profile
    - POST /api/v1/profiles/ - Create profile
    - PUT/PATCH /api/v1/profiles/{id}/ - Update profile
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ApplicantProfile.objects.all()
        return ApplicantProfile.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'my_profile':
            return CompleteProfileSerializer
        elif self.action == 'list':
            return ProfileSummarySerializer
        return ApplicantProfileSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def my_profile(self, request):
        """Get or update current user's profile"""
        try:
            profile = request.user.profile
        except ApplicantProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found. Please create your profile first.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'GET':
            serializer = CompleteProfileSerializer(profile)
            return Response(serializer.data)
        
        else:  # PUT or PATCH
            serializer = ApplicantProfileSerializer(
                profile, 
                data=request.data, 
                partial=(request.method == 'PATCH')
            )
            if serializer.is_valid():
                serializer.save()
                return Response(CompleteProfileSerializer(profile).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EducationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing education records
    Automatically filters by current user's profile
    """
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Education.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class WorkExperienceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing work experience records"""
    serializer_class = WorkExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WorkExperience.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class SkillViewSet(viewsets.ModelViewSet):
    """ViewSet for managing skills"""
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Skill.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple skills at once"""
        serializer = BulkSkillsSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            skills = serializer.save()
            return Response(
                SkillSerializer(skills, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get skills grouped by type"""
        skills = self.get_queryset()
        skill_types = {}
        for skill in skills:
            if skill.skill_type not in skill_types:
                skill_types[skill.skill_type] = []
            skill_types[skill.skill_type].append(SkillSerializer(skill).data)
        return Response(skill_types)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for managing projects"""
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Project.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class CertificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing certifications"""
    serializer_class = CertificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Certification.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class SocialLinkViewSet(viewsets.ModelViewSet):
    """ViewSet for managing social links"""
    serializer_class = SocialLinkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SocialLink.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class JobPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing job preferences"""
    serializer_class = JobPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return JobPreference.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


# Custom API Views (Non-ViewSet)
class ResumeUploadView(APIView):
    """Handle resume file uploads"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        try:
            profile = request.user.profile
            resume_file = request.FILES.get('resume')
            
            if not resume_file:
                return Response(
                    {'error': 'No resume file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file type and size
            allowed_types = ['pdf', 'doc', 'docx']
            file_extension = resume_file.name.split('.')[-1].lower()
            
            if file_extension not in allowed_types:
                return Response(
                    {'error': 'Only PDF, DOC, and DOCX files are allowed'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if resume_file.size > 5 * 1024 * 1024:  # 5MB limit
                return Response(
                    {'error': 'File size should not exceed 5MB'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            profile.resume = resume_file
            profile.resume_updated_at = timezone.now()
            profile.save()
            
            return Response({
                'message': 'Resume uploaded successfully',
                'resume_url': profile.resume.url if profile.resume else None
            })
            
        except ApplicantProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ProfilePhotoUploadView(APIView):
    """Handle profile photo uploads"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        try:
            profile = request.user.profile
            photo_file = request.FILES.get('photo')
            
            if not photo_file:
                return Response(
                    {'error': 'No photo file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file type and size
            allowed_types = ['jpg', 'jpeg', 'png']
            file_extension = photo_file.name.split('.')[-1].lower()
            
            if file_extension not in allowed_types:
                return Response(
                    {'error': 'Only JPG, JPEG, and PNG files are allowed'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if photo_file.size > 2 * 1024 * 1024:  # 2MB limit
                return Response(
                    {'error': 'File size should not exceed 2MB'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            profile.profile_picture = photo_file
            profile.save()
            
            return Response({
                'message': 'Profile photo uploaded successfully',
                'photo_url': profile.profile_picture.url if profile.profile_picture else None
            })
            
        except ApplicantProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class LocationListView(APIView):
    """Get list of available locations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        search = request.query_params.get('search', '')
        locations = Location.objects.all()
        
        if search:
            locations = locations.filter(
                Q(city__icontains=search) | Q(state__icontains=search)
            )
        
        locations = locations[:20]  # Limit results
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)


class IndustryListView(APIView):
    """Get list of available industries"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        industries = Industry.objects.all()
        serializer = IndustrySerializer(industries, many=True)
        return Response(serializer.data)


class DashboardStatsView(APIView):
    """Get dashboard statistics for the user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.profile
            
            stats = {
                'profile_completion': profile.profile_completion,
                'total_experience': profile.get_experience_display(),
                'education_count': profile.education.count(),
                'experience_count': profile.work_experience.count(),
                'skills_count': profile.skills.count(),
                'projects_count': profile.projects.count(),
                'certifications_count': profile.certifications.count(),
                'is_profile_public': profile.is_profile_public,
                'is_available_for_jobs': profile.is_available_for_jobs,
            }
            
            return Response(stats)
            
        except ApplicantProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class RecentActivityView(APIView):
    """Get recent activity for dashboard"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.profile
            
            # Get recent additions (last 30 days)
            from datetime import datetime, timedelta
            last_30_days = datetime.now() - timedelta(days=30)
            
            recent_activity = []
            
            # Recent education additions
            recent_education = profile.education.filter(
                id__in=Education.objects.filter(profile=profile).order_by('-id')[:3]
            )
            for edu in recent_education:
                recent_activity.append({
                    'type': 'education',
                    'title': f"Added {edu.degree_name}",
                    'description': f"at {edu.institution}",
                    'date': edu.id  # You might want to add created_at field
                })
            
            # Recent work experience
            recent_work = profile.work_experience.filter(
                id__in=WorkExperience.objects.filter(profile=profile).order_by('-id')[:3]
            )
            for work in recent_work:
                recent_activity.append({
                    'type': 'experience',
                    'title': f"Added {work.job_title}",
                    'description': f"at {work.company_name}",
                    'date': work.id
                })
            
            # Recent skills
            recent_skills = profile.skills.filter(
                id__in=Skill.objects.filter(profile=profile).order_by('-id')[:5]
            )
            if recent_skills:
                skill_names = [skill.name for skill in recent_skills]
                recent_activity.append({
                    'type': 'skills',
                    'title': "Added skills",
                    'description': ", ".join(skill_names),
                    'date': max([skill.id for skill in recent_skills])
                })
            
            # Sort by date (using id as proxy)
            recent_activity = sorted(recent_activity, key=lambda x: x['date'], reverse=True)[:10]
            
            return Response(recent_activity)
            
        except ApplicantProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ProfileCompletionView(APIView):
    """Get profile completion details"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.profile
            
            completion_details = {
                'overall_completion': profile.profile_completion,
                'sections': {
                    'basic_info': {
                        'completed': bool(profile.first_name and profile.last_name and profile.email and profile.phone),
                        'fields': ['first_name', 'last_name', 'email', 'phone'],
                        'weight': 20
                    },
                    'professional_summary': {
                        'completed': bool(profile.headline and profile.summary),
                        'fields': ['headline', 'summary'],
                        'weight': 15
                    },
                    'experience': {
                        'completed': profile.work_experience.exists(),
                        'count': profile.work_experience.count(),
                        'weight': 20
                    },
                    'education': {
                        'completed': profile.education.exists(),
                        'count': profile.education.count(),
                        'weight': 15
                    },
                    'skills': {
                        'completed': profile.skills.exists(),
                        'count': profile.skills.count(),
                        'weight': 15
                    },
                    'resume': {
                        'completed': bool(profile.resume),
                        'weight': 10
                    },
                    'profile_picture': {
                        'completed': bool(profile.profile_picture),
                        'weight': 5
                    }
                }
            }
            
            return Response(completion_details)
            
        except ApplicantProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )