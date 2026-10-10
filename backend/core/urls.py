"""
URL configuration for core project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = getattr(user, 'role', 'client')
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['username'] = user.username
        data['role'] = getattr(user, 'role', 'client')
        data['id'] = user.id
        data['is_staff_role'] = getattr(user, 'is_staff_role', False)
        data['is_client_role'] = getattr(user, 'is_client_role', False)
        membre = getattr(user, 'membre', None)
        data['membre_id'] = membre.id if membre else None
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('library.urls')),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
