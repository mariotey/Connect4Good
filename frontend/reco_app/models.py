from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime

# Create your models here.
class User(AbstractUser):
    pass

class Event(models.Model):
    name = models.CharField(max_length=600)
    description = models.CharField(max_length=6000)
    location = models.CharField(max_length=6000)
    start_datetime = models.DateTimeField()
    start_date = models.DateField()
    start_time = models.TimeField()
    end_datetime = models.DateTimeField()
    end_date = models.DateField()
    end_time = models.TimeField()
    created_datetime = models.DateTimeField(default=datetime.now)
    link = models.URLField(max_length = 6000) 

    def __str__(self):
        return f"{self.name}, {self.start_datetime}, {self.end_datetime}"

class Reco(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"
