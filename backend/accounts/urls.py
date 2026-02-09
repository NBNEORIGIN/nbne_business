from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # JWT token endpoints
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Current user
    path('me/', views.me, name='auth_me'),
    path('me/update/', views.update_me, name='auth_update_me'),
    path('me/password/', views.change_password, name='auth_change_password'),
    path('me/set-password/', views.set_password, name='auth_set_password'),
    # User management (admin)
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/role/', views.user_update_role, name='user_update_role'),
    path('users/<int:user_id>/deactivate/', views.user_deactivate, name='user_deactivate'),
]
