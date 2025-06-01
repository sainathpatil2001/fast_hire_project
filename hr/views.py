# hr/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsHR

class HRDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def get(self, request):
        return Response({
            "message": "Welcome HR!",
            "email": request.user.email,
            "role": request.user.role
        })
