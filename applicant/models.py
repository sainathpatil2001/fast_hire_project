from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import json
from django.conf import settings

# Core Profile Model
class ApplicantProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    
    EMPLOYMENT_STATUS = [
        ('employed', 'Currently Employed'),
        ('unemployed', 'Unemployed'),
        ('student', 'Student'),
        ('freelancer', 'Freelancer'),
        ('self_employed', 'Self Employed'),
    ]
    
    NOTICE_PERIOD = [
        ('immediate', 'Immediate'),
        ('15_days', '15 Days'),
        ('1_month', '1 Month'),
        ('2_months', '2 Months'),
        ('3_months', '3 Months'),
        ('more_than_3', 'More than 3 Months'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Basic Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    # Profile Picture
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Location
    current_city = models.CharField(max_length=100)
    current_state = models.CharField(max_length=100)
    current_country = models.CharField(max_length=100, default='India')
    preferred_locations = models.ManyToManyField('Location', blank=True)
    
    # Professional Summary
    headline = models.CharField(max_length=200, help_text="Professional headline")
    summary = models.TextField(max_length=2000, help_text="Professional summary")
    
    # Career Information
    total_experience_years = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    total_experience_months = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(11)])
    current_employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS)
    notice_period = models.CharField(max_length=20, choices=NOTICE_PERIOD, blank=True)
    
    # Salary Information
    current_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Resume
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    resume_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Profile Completion
    profile_completion = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_profile_public = models.BooleanField(default=True)
    is_available_for_jobs = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applicant_profiles'
        
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_experience_display(self):
        years = "year" if self.total_experience_years == 1 else "years"
        months = "month" if self.total_experience_months == 1 else "months"
        if self.total_experience_years > 0 and self.total_experience_months > 0:
            return f"{self.total_experience_years} {years} {self.total_experience_months} {months}"
        elif self.total_experience_years > 0:
            return f"{self.total_experience_years} {years}"
        elif self.total_experience_months > 0:
            return f"{self.total_experience_months} {months}"
        return "Fresher"


# Location Model
class Location(models.Model):
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    
    class Meta:
        db_table = 'locations'
        unique_together = ['city', 'state', 'country']
    
    def __str__(self):
        return f"{self.city}, {self.state}"


# Education Model
class Education(models.Model):
    DEGREE_TYPES = [
        ('high_school', 'High School'),
        ('diploma', 'Diploma'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD'),
        ('certification', 'Certification'),
    ]
    
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='education')
    degree_type = models.CharField(max_length=20, choices=DEGREE_TYPES)
    degree_name = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200, blank=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'education'
        ordering = ['-end_year', '-start_year']
    
    def __str__(self):
        return f"{self.degree_name} from {self.institution}"


# Work Experience Model
class WorkExperience(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]
    
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='work_experience')
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES)
    location = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField()
    key_achievements = models.TextField(blank=True)
    
    class Meta:
        db_table = 'work_experience'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"


# Skills Model
class Skill(models.Model):
    SKILL_TYPES = [
        ('technical', 'Technical'),
        ('soft', 'Soft Skills'),
        ('language', 'Language'),
        ('tool', 'Tools & Software'),
    ]
    
    PROFICIENCY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    skill_type = models.CharField(max_length=20, choices=SKILL_TYPES)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_LEVELS)
    years_of_experience = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        db_table = 'skills'
        unique_together = ['profile', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.proficiency}"


# Projects Model
class Project(models.Model):
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    technologies_used = models.TextField(help_text="Comma separated technologies")
    project_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_ongoing = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'projects'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title


# Certifications Model
class Certification(models.Model):
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)
    
    class Meta:
        db_table = 'certifications'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.name} by {self.issuing_organization}"


# Job Preferences Model (Updated to work with SQLite)
class JobPreference(models.Model):
    JOB_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
        ('remote', 'Remote'),
    ]
    
    WORK_MODES = [
        ('office', 'Work from Office'),
        ('remote', 'Work from Home'),
        ('hybrid', 'Hybrid'),
    ]
    
    profile = models.OneToOneField(ApplicantProfile, on_delete=models.CASCADE, related_name='job_preferences')
    # Replace JSONField with TextField for SQLite compatibility
    preferred_job_types = models.TextField(default='[]', help_text="JSON formatted job types")
    preferred_work_modes = models.TextField(default='[]', help_text="JSON formatted work modes")
    preferred_industries = models.ManyToManyField('Industry', blank=True)
    preferred_companies = models.TextField(blank=True, help_text="Comma separated company names")
    min_salary_expectation = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_salary_expectation = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'job_preferences'
    
    def __str__(self):
        return f"Job preferences for {self.profile.get_full_name()}"
    
    # Helper methods for job types
    def set_preferred_job_types(self, job_types_list):
        """Store list of job types as JSON string"""
        self.preferred_job_types = json.dumps(job_types_list)
    
    def get_preferred_job_types(self):
        """Retrieve job types as list"""
        try:
            return json.loads(self.preferred_job_types) if self.preferred_job_types else []
        except json.JSONDecodeError:
            return []
    
    # Helper methods for work modes
    def set_preferred_work_modes(self, work_modes_list):
        """Store list of work modes as JSON string"""
        self.preferred_work_modes = json.dumps(work_modes_list)
    
    def get_preferred_work_modes(self):
        """Retrieve work modes as list"""
        try:
            return json.loads(self.preferred_work_modes) if self.preferred_work_modes else []
        except json.JSONDecodeError:
            return []
    
    # Helper method for companies
    def set_preferred_companies_list(self, companies_list):
        """Convert list to comma-separated string"""
        self.preferred_companies = ', '.join(companies_list)
    
    def get_preferred_companies_list(self):
        """Convert comma-separated string to list"""
        return [company.strip() for company in self.preferred_companies.split(',') if company.strip()]


# Industry Model
class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'industries'
        verbose_name_plural = 'Industries'
    
    def __str__(self):
        return self.name


# Social Links Model
class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('github', 'GitHub'),
        ('twitter', 'Twitter'),
        ('portfolio', 'Portfolio Website'),
        ('stackoverflow', 'Stack Overflow'),
        ('behance', 'Behance'),
        ('dribbble', 'Dribbble'),
        ('other', 'Other'),
    ]
    
    profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()
    
    class Meta:
        db_table = 'social_links'
        unique_together = ['profile', 'platform']
    
    def __str__(self):
        return f"{self.platform} - {self.profile.get_full_name()}"