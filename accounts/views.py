from django.contrib.auth import authenticate, get_user_model, login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(APIView):
    """
    POST /api/auth/register/
    S1-T1: Register new user with role (S1-T2)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'message': 'User registered successfully.',
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/auth/login/
    S1-T1: Session-based login
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return Response(
            {
                'message': 'Login successful.',
                'user': UserSerializer(user).data,
            }
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    S1-T1: Session-based logout
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful.'})


class MeView(APIView):
    """
    GET /api/auth/me/
    Returns current user info + role
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
