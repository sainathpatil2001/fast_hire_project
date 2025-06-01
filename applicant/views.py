# accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsApplicant

class ApplicantDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsApplicant]

    def get(self, request):
        return Response({
            "message": "Welcome, applicant!",
            "email": request.user.email,
            "role": request.user.role
        })
