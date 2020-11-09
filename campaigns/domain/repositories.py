from __future__ import annotations

from asyncio.tasks import gather
import dataclasses
import json
from typing import Any, Generic, List, Optional, TypeVar, TYPE_CHECKING

import aioredis
from asgiref.sync import sync_to_async
from campaigns import models
from dacite import from_dict
from dacite.exceptions import DaciteError
from typing_extensions import Protocol

from .entities import Campaign, Event

if TYPE_CHECKING:
    from api.views import DataFetchingStats


class WithId(Protocol):
    id: Any


class BaseRedisRepository:
    DEFAULT_EXPIRE_IN_SECONDS = 5

    def __init__(
        self, redis: aioredis.Redis, data_fetching_stats: DataFetchingStats
    ) -> None:
        self.redis = redis
        self.data_fetching_stats = data_fetching_stats

    async def _cache_entity(self, entity: WithId):
        self.data_fetching_stats.number_of_redis_sets += 1

        await self.redis.set(
            f"{type(entity).__name__}-{entity.id}",
            json.dumps(dataclasses.asdict(entity)),
            expire=self.DEFAULT_EXPIRE_IN_SECONDS,
        )

    async def _get_cached_entity(self, id: Any, entity_class: Any) -> Optional[Any]:
        self.data_fetching_stats.number_of_redis_gets += 1

        entity = await self.redis.get(f"{entity_class.__name__}-{id}")

        if not entity:
            return None

        try:
            return from_dict(Campaign, json.loads(entity))
        except DaciteError:
            # TODO: log this

            return None


class CampaignRepository(BaseRedisRepository):
    @sync_to_async
    def _get_campaign_from_db(self, id: str) -> Optional[models.Campaign]:
        self.data_fetching_stats.number_of_sql_calls += 1

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

    @sync_to_async
    def _get_campaigns_ids(self, first: int) -> List[Campaign]:
        self.data_fetching_stats.number_of_sql_calls += 1

        return list(models.Campaign.objects.all().values_list("id", flat=True)[:first])

    async def get_campaigns(self, first: int) -> List[Campaign]:
        ids = await self._get_campaigns_ids(first)

        return await gather(*(self.get_campaign_by_id(id) for id in ids))


class EventRepository(BaseRedisRepository):
    @sync_to_async
    def get_events_for_campaign(self, campaign_id: str) -> List[Event]:
        self.data_fetching_stats.number_of_sql_calls += 1
        db_events = models.Event.objects.filter(campaign__id=campaign_id).all()

        return [Event(id=e.id, title=e.title) for e in db_events]

    @sync_to_async
    def get_event_ids(self, campaign_id: str, first: int) -> List[str]:
        self.data_fetching_stats.number_of_sql_calls += 1

        return list(
            models.Event.objects.filter(campaign__id=campaign_id).values_list(
                "id", flat=True
            )[:first]
        )

    @sync_to_async
    def get_events_batch(self, event_ids: List[str]) -> List[List[Event]]:
        self.data_fetching_stats.number_of_sql_calls += 1

        return list(models.Event.objects.filter(id__in=event_ids))
