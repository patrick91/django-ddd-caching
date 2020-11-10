from __future__ import annotations

import dataclasses
import json
from asyncio.tasks import gather
from typing import TYPE_CHECKING, Any, List, Optional, Type

import aioredis
from asgiref.sync import sync_to_async
from campaigns import models
from typing_extensions import Protocol

from .entities import Campaign, Event, convert_dict_to_entity, EntityType

if TYPE_CHECKING:
    from api.views import DataFetchingStats


class WithId(Protocol):
    id: Any


def increase_sql_queries(fn):
    def wrap(self, *args, **kwargs):
        self.data_fetching_stats.number_of_sql_calls += 1

        return fn(self, *args, **kwargs)

    return wrap


def increase_redis_sets(fn):
    def wrap(self, *args, **kwargs):
        self.data_fetching_stats.number_of_redis_sets += 1

        return fn(self, *args, **kwargs)

    return wrap


def increase_redis_gets(fn):
    def wrap(self, *args, **kwargs):
        self.data_fetching_stats.number_of_redis_gets += 1

        return fn(self, *args, **kwargs)

    return wrap


class BaseRedisRepository:
    DEFAULT_EXPIRE_IN_SECONDS = 5

    def __init__(
        self, redis: aioredis.Redis, data_fetching_stats: DataFetchingStats
    ) -> None:
        self.redis = redis
        self.data_fetching_stats = data_fetching_stats

    @increase_redis_sets
    async def _cache_entity(self, entity: WithId):
        await self.redis.set(
            f"{type(entity).__name__}-{entity.id}",
            json.dumps(dataclasses.asdict(entity)),
            expire=self.DEFAULT_EXPIRE_IN_SECONDS,
        )

    @increase_redis_sets
    async def _cache_entities_batch(self, entities: List[WithId]):
        entities_dict = {
            f"{type(entity).__name__}-{entity.id}": json.dumps(
                dataclasses.asdict(entity)
            )
            for entity in entities
        }

        # TODO: set expiry

        await self.redis.mset(
            entities_dict,
            # expire=self.DEFAULT_EXPIRE_IN_SECONDS,
        )

    @increase_redis_gets
    async def _get_cached_entity(
        self, id: Any, entity_class: Type[EntityType]
    ) -> Optional[EntityType]:
        entity = await self.redis.get(f"{entity_class.__name__}-{id}")

        return convert_dict_to_entity(entity, entity_class)

    @increase_redis_gets
    async def _get_cached_entities_batch(
        self, ids: List[Any], entity_class: Type[EntityType]
    ) -> List[Optional[EntityType]]:
        keys = [f"{entity_class.__name__}-{id}" for id in ids]

        entities = await self.redis.mget(*keys)

        return [convert_dict_to_entity(entity, entity_class) for entity in entities]


class CampaignRepository(BaseRedisRepository):
    @increase_sql_queries
    @sync_to_async
    def _get_campaign_from_db(self, id: str) -> Optional[models.Campaign]:
        return models.Campaign.objects.filter(id=id).first()

    async def get_campaign_by_id(self, id: str) -> Optional[Campaign]:
        campaign_entity = await self._get_cached_entity(id, Campaign)

        if campaign_entity:
            return campaign_entity

        db_campaign = await self._get_campaign_from_db(id)

        if not db_campaign:
            return None

        campaign_entity = Campaign(id=str(db_campaign.id), title=db_campaign.title)

        await self._cache_entity(campaign_entity)

        return campaign_entity

    @increase_sql_queries
    @sync_to_async
    def _get_campaigns_ids(self, first: int) -> List[Campaign]:
        return list(models.Campaign.objects.all().values_list("id", flat=True)[:first])

    async def get_campaigns(self, first: int) -> List[Campaign]:
        ids = await self._get_campaigns_ids(first)

        return await gather(*(self.get_campaign_by_id(id) for id in ids))


class EventRepository(BaseRedisRepository):
    @increase_sql_queries
    @sync_to_async
    def get_events_for_campaign(self, campaign_id: str) -> List[Event]:
        db_events = models.Event.objects.filter(campaign__id=campaign_id).all()

        return [Event(id=e.id, title=e.title) for e in db_events]

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
    def _get_event_from_db(self, id: str) -> Optional[models.Event]:
        return models.Event.objects.filter(id=id).first()

    @increase_sql_queries
    @sync_to_async
    def _get_events_from_db(self, ids: List[str]) -> List[models.Event]:
        return list(models.Event.objects.filter(id__in=ids))

    async def get_event_by_id(self, id: str) -> Optional[Event]:
        event_entity = await self._get_cached_entity(id, Event)

        if event_entity:
            return event_entity

        db_event = await self._get_event_from_db(id)

        if not db_event:
            return None

        event_entity = Event(id=str(db_event.id), title=db_event.title)

        await self._cache_entity(event_entity)

        return event_entity

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
            entity = Event(id=str(db_event.id), title=db_event.title)

            missing_entities.append(entity)
            entities_dict[str(db_event.id)] = entity

        await self._cache_entities_batch(missing_entities)

        return list(entities_dict.values())
