import django_filters
from tasks.models import Task


class TaskFilter(django_filters.FilterSet):

    # Filter by task state.
    state = django_filters.CharFilter(field_name="state")

    # Filter by priority.
    priority = django_filters.BooleanFilter(field_name="priority")

    # Tasks due after date.
    deadline_after = django_filters.DateTimeFilter(
        field_name="deadline", lookup_expr="gte"
    )

    # Tasks due before date.
    deadline_before = django_filters.DateTimeFilter(
        field_name="deadline", lookup_expr="lte"
    )

    # Assigned to me
    assigned_to_me = django_filters.BooleanFilter(method="filter_assigned_to_me", field_name="assigned_to")

    class Meta:
        model = Task
        fields = ["state", "priority", "assigned_to_me"]

    def filter_assigned_to_me(self, queryset, name, value):
        if value:
            return queryset.filter(assigned_to=self.request.user)

        return queryset
