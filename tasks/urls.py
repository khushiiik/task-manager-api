from django.urls import path
from rest_framework.routers import DefaultRouter
from tasks.views import TasksViewSet, OverdueTaskReportView

router = DefaultRouter()

router.register("", TasksViewSet, basename="tasks-detail")

urlpatterns = router.urls + [
    path("reports/overdue/", OverdueTaskReportView.as_view(), name="overdue-task-report"),
]