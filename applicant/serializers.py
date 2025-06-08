# applicant/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ApplicantProfile, Location, Education, WorkExperience, 
    Skill, Project, Certification, JobPreference, Industry, SocialLink
)

User = get_user_model()

# ======================== USER AUTH SERIALIZERS ========================

class ApplicantRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data.get('email'),
            password=validated_data['password'],
        )
        user.is_applicant = True
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']
        read_only_fields = ['id']

# ======================== PROFILE-RELATED SERIALIZERS ========================

class LocationSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = ['id', 'city', 'state', 'country', 'display_name']
    
    def get_display_name(self, obj):
        return f"{obj.city}, {obj.state}"

class EducationSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Education
        fields = [
            'id', 'degree_type', 'degree_name', 'institution', 
            'field_of_study', 'start_year', 'end_year', 'is_current',
            'percentage', 'cgpa', 'description', 'duration'
        ]
    
    def get_duration(self, obj):
        if obj.is_current:
            return f"{obj.start_year} - Present"
        elif obj.end_year:
            return f"{obj.start_year} - {obj.end_year}"
        return str(obj.start_year)
    
    def validate(self, data):
        if data.get('is_current') and data.get('end_year'):
            raise serializers.ValidationError("End year should not be provided for current education")
        if not data.get('is_current') and not data.get('end_year'):
            raise serializers.ValidationError("End year is required for completed education")
        return data

class WorkExperienceSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    experience_length = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkExperience
        fields = [
            'id', 'job_title', 'company_name', 'employment_type',
            'location', 'start_date', 'end_date', 'is_current',
            'description', 'key_achievements', 'duration', 'experience_length'
        ]
    
    def get_duration(self, obj):
        if obj.is_current:
            return f"{obj.start_date.strftime('%b %Y')} - Present"
        elif obj.end_date:
            return f"{obj.start_date.strftime('%b %Y')} - {obj.end_date.strftime('%b %Y')}"
        return obj.start_date.strftime('%b %Y')
    
    def get_experience_length(self, obj):
        from datetime import date
        end_date = obj.end_date if obj.end_date else date.today()
        delta = end_date - obj.start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        return f"{years}y {months}m" if years else f"{months}m"
    
    def validate(self, data):
        if data.get('is_current') and data.get('end_date'):
            raise serializers.ValidationError("End date should not be provided for current job")
        if not data.get('is_current') and not data.get('end_date'):
            raise serializers.ValidationError("End date is required for completed job")
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("Start date cannot be after end date")
        return data

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'skill_type', 'proficiency', 'years_of_experience']
    
    def validate_name(self, value):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            profile = request.user.profile
            existing_skill = Skill.objects.filter(
                profile=profile, name__iexact=value
            ).exclude(id=self.instance.id if self.instance else None)
            if existing_skill.exists():
                raise serializers.ValidationError("You already have this skill in your profile")
        return value

class ProjectSerializer(serializers.ModelSerializer):
    technologies_list = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'technologies_used', 'technologies_list',
            'project_url', 'github_url', 'start_date', 'end_date', 
            'is_ongoing', 'duration'
        ]
    
    def get_technologies_list(self, obj):
        return [tech.strip() for tech in obj.technologies_used.split(',')] if obj.technologies_used else []
    
    def get_duration(self, obj):
        if obj.is_ongoing:
            return f"{obj.start_date.strftime('%b %Y')} - Present"
        elif obj.end_date:
            return f"{obj.start_date.strftime('%b %Y')} - {obj.end_date.strftime('%b %Y')}"
        return obj.start_date.strftime('%b %Y')

class CertificationSerializer(serializers.ModelSerializer):
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Certification
        fields = [
            'id', 'name', 'issuing_organization', 'issue_date',
            'expiry_date', 'credential_id', 'credential_url', 'is_expired'
        ]
    
    def get_is_expired(self, obj):
        from datetime import date
        return obj.expiry_date and obj.expiry_date < date.today()

class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ['id', 'platform', 'url']
    
    def validate_url(self, value):
        import re
        platform = self.initial_data.get('platform')
        patterns = {
            'linkedin': r'linkedin\.com',
            'github': r'github\.com',
            'twitter': r'twitter\.com',
            'stackoverflow': r'stackoverflow\.com',
        }
        if platform in patterns and not re.search(patterns[platform], value):
            raise serializers.ValidationError(f"Please provide a valid {platform} URL")
        return value

class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ['id', 'name', 'description']

class JobPreferenceSerializer(serializers.ModelSerializer):
    preferred_industries = IndustrySerializer(many=True, read_only=True)
    preferred_industry_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    preferred_companies_list = serializers.SerializerMethodField()
    salary_range = serializers.SerializerMethodField()
    
    class Meta:
        model = JobPreference
        fields = [
            'preferred_job_types', 'preferred_work_modes', 'preferred_industries',
            'preferred_industry_ids', 'preferred_companies', 'preferred_companies_list',
            'min_salary_expectation', 'max_salary_expectation', 'salary_range'
        ]
    
    def get_preferred_companies_list(self, obj):
        return [company.strip() for company in obj.preferred_companies.split(',')] if obj.preferred_companies else []
    
    def get_salary_range(self, obj):
        if obj.min_salary_expectation and obj.max_salary_expectation:
            return f"₹{obj.min_salary_expectation} - ₹{obj.max_salary_expectation}"
        elif obj.min_salary_expectation:
            return f"₹{obj.min_salary_expectation}+"
        return None
    
    def update(self, instance, validated_data):
        industry_ids = validated_data.pop('preferred_industry_ids', None)
        instance = super().update(instance, validated_data)
        if industry_ids is not None:
            industries = Industry.objects.filter(id__in=industry_ids)
            instance.preferred_industries.set(industries)
        return instance

class ApplicantProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    experience_display = serializers.SerializerMethodField()
    preferred_locations = LocationSerializer(many=True, read_only=True)
    preferred_location_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = ApplicantProfile
        fields = [
            'id', 'user', 'full_name', 'email', 
            'phone', 'date_of_birth', 'age', 'gender', 'profile_picture',
            'current_city', 'current_state', 'current_country', 
            'preferred_locations', 'preferred_location_ids',
            'headline', 'summary', 'total_experience_years', 
            'total_experience_months', 'experience_display',
            'current_employment_status', 'notice_period',
            'current_salary', 'expected_salary', 'resume', 'resume_updated_at',
            'profile_completion', 'is_profile_public', 'is_available_for_jobs',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'profile_completion', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_experience_display(self, obj):
        return obj.get_experience_display()
    
    def get_age(self, obj):
        from datetime import date
        if obj.date_of_birth:
            today = date.today()
            return today.year - obj.date_of_birth.year - (
                (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
            )
        return None
    
    def update(self, instance, validated_data):
        location_ids = validated_data.pop('preferred_location_ids', None)
        instance = super().update(instance, validated_data)
        if location_ids is not None:
            locations = Location.objects.filter(id__in=location_ids)
            instance.preferred_locations.set(locations)
        instance.profile_completion = self.calculate_profile_completion(instance)
        instance.save()
        return instance
    
    def calculate_profile_completion(self, profile):
        total_fields = 20
        completed_fields = 0
        basic_fields = [  profile.email, profile.phone, profile.current_city, profile.headline]
        completed_fields += sum(1 for field in basic_fields if field)
        if profile.date_of_birth: completed_fields += 1
        if profile.profile_picture: completed_fields += 1
        if profile.summary: completed_fields += 1
        if profile.resume: completed_fields += 1
        if profile.current_employment_status: completed_fields += 1
        if profile.total_experience_years or profile.total_experience_months: completed_fields += 1
        if profile.education.exists(): completed_fields += 2
        if profile.work_experience.exists(): completed_fields += 2
        if profile.skills.exists(): completed_fields += 2
        if profile.preferred_locations.exists(): completed_fields += 1
        if hasattr(profile, 'job_preferences'): completed_fields += 2
        if profile.social_links.exists(): completed_fields += 1
        return min(int((completed_fields / total_fields) * 100), 100)

class CompleteProfileSerializer(ApplicantProfileSerializer):
    education = EducationSerializer(many=True, read_only=True)
    work_experience = WorkExperienceSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    social_links = SocialLinkSerializer(many=True, read_only=True)
    job_preferences = JobPreferenceSerializer(read_only=True)
    
    class Meta(ApplicantProfileSerializer.Meta):
        fields = ApplicantProfileSerializer.Meta.fields + [
            'education', 'work_experience', 'skills', 'projects',
            'certifications', 'social_links', 'job_preferences'
        ]

class ProfileSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    experience_display = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    top_skills = serializers.SerializerMethodField()
    
    class Meta:
        model = ApplicantProfile
        fields = [
            'id', 'full_name', 'headline', 'profile_picture',
            'experience_display', 'location', 'current_employment_status',
            'expected_salary', 'is_available_for_jobs', 'top_skills'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_experience_display(self, obj):
        return obj.get_experience_display()
    
    def get_location(self, obj):
        return f"{obj.current_city}, {obj.current_state}"
    
    def get_top_skills(self, obj):
        return list(obj.skills.values_list('name', flat=True)[:5])

class BulkSkillsSerializer(serializers.Serializer):
    skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        max_length=50
    )
    skill_type = serializers.ChoiceField(choices=Skill.SKILL_TYPES)
    proficiency = serializers.ChoiceField(choices=Skill.PROFICIENCY_LEVELS)
    
    def create(self, validated_data):
        profile = self.context['request'].user.profile
        skills_data = validated_data['skills']
        skill_type = validated_data['skill_type']
        proficiency = validated_data['proficiency']
        
        created_skills = []
        for skill_name in skills_data:
            skill, created = Skill.objects.get_or_create(
                profile=profile,
                name=skill_name,
                defaults={
                    'skill_type': skill_type,
                    'proficiency': proficiency,
                    'years_of_experience': 0
                }
            )
            if created:
                created_skills.append(skill)
        
        return created_skills
