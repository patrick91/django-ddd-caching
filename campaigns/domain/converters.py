from typing import Any, Callable

from campaigns import models
from django.db.models.base import Model

from .entities import Campaign, Event


def convert_campaign(
    campaign: models.Campaign, convert_django_model: Callable[[Model], Any]
) -> Campaign:
    return Campaign(id=str(campaign.id), title=campaign.title)


def convert_event(
    event: models.Event, convert_django_model: Callable[[Model], Any]
) -> Event:
    return Event(id=str(event.id), title=event.title)
