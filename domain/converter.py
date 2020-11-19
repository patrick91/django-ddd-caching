from functools import singledispatch
from typing import Any

from campaigns.domain import entities as campaign_entities
from campaigns.domain.converters import convert_brand, convert_campaign, convert_event
from campaigns.models import Campaign, Event, Brand
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import Model


@singledispatch
def convert_django_model(instance: Model) -> Any:
    raise ImproperlyConfigured(
        f"Don't know how to convert the model {instance.__class__}"
    )


@convert_django_model.register
def _campaign(instance: Campaign) -> campaign_entities.Campaign:
    return convert_campaign(instance, convert_django_model)


@convert_django_model.register
def _event(instance: Event) -> campaign_entities.Event:
    return convert_event(instance, convert_django_model)


@convert_django_model.register
def _brand(instance: Brand) -> campaign_entities.Brand:
    return convert_brand(instance, convert_django_model)


__all__ = ["convert_django_model"]