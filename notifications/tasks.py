from celery import shared_task
from notifications.models import Notification 
from accounts.models import User

@shared_task
def create_notification(user_id, message):

    user = User.objects.get(id=user_id)

    Notification.objects.create(
        user = user,
        message = message
    )