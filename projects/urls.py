from rest_framework.routers import DefaultRouter
from projects import views

router = DefaultRouter()
router.register("", views.ProjectViewSet, basename="projects-detail")

urlpatterns = router.urls
