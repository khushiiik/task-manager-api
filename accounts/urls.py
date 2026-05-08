from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from accounts import views

urlpatterns = [
    # Auth.
    path("login/", jwt_views.TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh", jwt_views.TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/change-password/", views.ChangePasswordView.as_view(), name="change-pasword"),
    # Profile.
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # Admin User Management.
    path("", views.UserView.as_view(), name="user-view"),
    path("<int:pk>/", views.UserDetailView.as_view()),
]
