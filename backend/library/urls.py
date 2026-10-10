from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'livres', views.LivreViewSet, basename='livre')
router.register(r'categories', views.CategorieViewSet, basename='categorie')
router.register(r'emprunts', views.EmpruntViewSet, basename='emprunt')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'membres', views.MembreViewSet, basename='membre')

urlpatterns = [
    # Pages HTML (Vanilla JS)
    path('', views.home_page, name='home'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('livres/', views.livres_page, name='livres'),
    path('membres/', views.membres_page, name='membres'),
    path('emprunts/', views.emprunts_page, name='emprunts'),
    path('categories/', views.categories_page, name='categories'),

    # API JSON pour fetch()
    path('api/auth/register/', views.RegisterView.as_view(), name='register-api'),
    path('api/', include(router.urls)),
]
