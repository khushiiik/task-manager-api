from rest_framework.routers import DefaultRouter
from tasks.views import TasksViewSet

router = DefaultRouter()

router.register("", TasksViewSet, basename="tasks-detail")

urlpatterns = router.urls
