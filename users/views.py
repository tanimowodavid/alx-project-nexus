from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import RetrieveUpdateAPIView
from .serializers import UserCreateSerializer, UserSerializer, UserUpdateSerializer, ChangePasswordSerializer, LogoutSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone


# Register a new user
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View and update user profile
class UserProfileView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


# Change user password
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({"message": "Password updated successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Logout view to blacklist refresh token
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Delete user account
class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        
        try:
            # Blacklist the current session's refresh token
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Perform Soft Delete logic
            user.first_name = "Deleted"
            user.last_name = "User"
            user.email = f"deleted-{timezone.now().timestamp()}@{user.email.split('@')[-1]}"
            user.is_active = False
            user.save()
            
            return Response({"detail": "Account deleted and logged out."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": "Refresh token required for logout"}, status=status.HTTP_400_BAD_REQUEST)
