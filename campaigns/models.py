from django.db import models


class Event(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.title


class Campaign(models.Model):
    title = models.CharField(max_length=200)
    events = models.ManyToManyField(Event)

    def __str__(self) -> str:
        return self.title
