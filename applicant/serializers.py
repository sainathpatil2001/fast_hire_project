# applicant/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class ApplicantRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
        )
        user.is_applicant = True  # Automatically set role
        user.save()
        return user
