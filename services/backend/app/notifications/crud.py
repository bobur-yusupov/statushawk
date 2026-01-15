from common.crud import FullCRUD
from .models import NotificationChannel, NotificationLog

class NotificationChannelCRUD(FullCRUD[NotificationChannel]):
    model = NotificationChannel

class NotificationLogCRUD(FullCRUD[NotificationLog]):
    model = NotificationLog
