from django.db import models


class Brand(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()

    def __str__(self) -> str:
        return self.title


class Campaign(models.Model):
    title = models.CharField(max_length=200)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT)
    events = models.ManyToManyField(Event)
    body = models.TextField()

    def __str__(self) -> str:
        return self.title
