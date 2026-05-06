from rest_framework.routers import DefaultRouter
from teams.views import TeamViewSet

router = DefaultRouter()
router.register("", TeamViewSet, basename="teams-detail")

urlpatterns = router.urls
