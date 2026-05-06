from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from accounts import views

urlpatterns = [
    path("", views.UserView.as_view(), name="user-view"),
    path("login/", jwt_views.TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh", jwt_views.TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("user-list/", views.UserListView.as_view(), name="user-list"),
    path("<int:pk>/", views.UserDetailView.as_view()),
]
