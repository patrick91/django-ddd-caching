from __future__ import annotations

from typing import List

from asgiref.sync import sync_to_async
from campaigns import models
from domain.converter import convert_django_model
from domain.repositories.cache import BaseCacheRepository
from domain.repositories.stats import increase_sql_queries

from ..entities import Event


class EventRepository(BaseCacheRepository):
    @increase_sql_queries
    @sync_to_async
    def get_events_for_campaign(self, campaign_id: str) -> List[Event]:
        db_events = models.Event.objects.filter(campaign__id=campaign_id).all()

        return [convert_django_model(e) for e in db_events]

    @increase_sql_queries
    @sync_to_async
    def get_event_ids(self, campaign_id: str, first: int) -> List[str]:
        return list(
            models.Event.objects.filter(campaign__id=campaign_id).values_list(
                "id", flat=True
            )[:first]
        )

    @increase_sql_queries
    @sync_to_async
    def _get_events_from_db(self, ids: List[str]) -> List[models.Event]:
        return list(models.Event.objects.filter(id__in=ids))

    async def get_events_batch(self, event_ids: List[str]) -> List[Event]:
        entities = await self._get_cached_entities_batch(event_ids, Event)

        if all(entities):
            return entities

        entities_dict = {}

        missing_events_ids = []

        for event_id, entity in zip(event_ids, entities):
            entities_dict[str(event_id)] = entity

            if not entity:
                missing_events_ids.append(event_id)

        missing_events_db = await self._get_events_from_db(missing_events_ids)
        missing_entities = []

        for db_event in missing_events_db:
            entity = convert_django_model(db_event)

            missing_entities.append(entity)
            entities_dict[str(db_event.id)] = entity

        await self._cache_entities_batch(missing_entities)

        return list(entities_dict.values())
