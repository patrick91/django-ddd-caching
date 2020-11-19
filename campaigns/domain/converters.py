from typing import Any, Callable

from campaigns import models
from django.db.models.base import Model

from .entities import Campaign, Event, Brand


def convert_brand(
    brand: models.Brand, convert_django_model: Callable[[Model], Any]
) -> Brand:
    return Brand(id=str(brand.id), name=brand.name)


def convert_campaign(
    campaign: models.Campaign, convert_django_model: Callable[[Model], Any]
) -> Campaign:
    return Campaign(
        id=str(campaign.id),
        title=campaign.title,
        body=campaign.body,
        brand_id=str(campaign.brand_id),
    )


def convert_event(
    event: models.Event, convert_django_model: Callable[[Model], Any]
) -> Event:
    return Event(id=str(event.id), title=event.title, body=event.body)
