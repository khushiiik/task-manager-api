import django_filters
from tasks.models import Task


class TaskFilter(django_filters.FilterSet):

    # Filter by task state.
    state = django_filters.CharFilter(field_name="state")

    # Filter by priority.
    priority = django_filters.CharFilter(field_name="priority")

    # Tasks due after date.
    deadline_after = django_filters.DateTimeFilter(
        field_name="deadline", lookup_expr="gte"
    )

    # Tasks due before date.
    deadline_before = django_filters.DateTimeFilter(
        field_name="deadline", lookup_expr="lte"
    )

    class Meta:
        model = Task
        fields = ["state", "priority"]
