from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

app_name = 'accounts'


class CustomTokenObtainPairView(TokenObtainPairView):
    """S2-T1: JWT login that returns tokens + user role."""
    serializer_class = CustomTokenObtainPairSerializer


urlpatterns = [
    # Session-based (for browsable API)
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.MeView.as_view(), name='me'),

    # S2-T1: JWT token endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
