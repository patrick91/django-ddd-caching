import dataclasses
import json
from typing import List, Optional

import aioredis
from asgiref.sync import sync_to_async
from campaigns import models
from dacite.exceptions import DaciteError
from dacite import from_dict

from .entities import Campaign, Event


class CampaignRepository:
    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis = redis

    @sync_to_async
    def _get_campaign_from_db(self, id: str) -> Optional[models.Campaign]:
        return models.Campaign.objects.filter(id=id).first()

    async def _cache_campaign(self, entity: Campaign):
        await self.redis.set(
            f"campaign-{entity.id}", json.dumps(dataclasses.asdict(entity))
        )

    async def _get_cached_campaign(self, id: str) -> Optional[Campaign]:
        campaign_entity = await self.redis.get(f"campaign-{id}")

        if not campaign_entity:
            return None

        try:
            return from_dict(Campaign, json.loads(campaign_entity))
        except DaciteError:
            # TODO: log this

            return None

    async def get_campaign_by_id(self, id: str) -> Optional[Campaign]:
        campaign_entity = await self._get_cached_campaign(id)

        if campaign_entity:

            return campaign_entity

        db_campaign = await self._get_campaign_from_db(id)

        if not db_campaign:
            return None

        campaign_entity = Campaign(id=str(db_campaign.id), title=db_campaign.title)

        await self._cache_campaign(campaign_entity)

        return campaign_entity

    @sync_to_async
    def get_campaigns(self, first: int) -> List[Campaign]:
        return list(models.Campaign.objects.all()[:first])


class EventRepository:
    @sync_to_async
    def get_events_for_campaign(self, campaign_id: str) -> List[Event]:
        db_events = models.Event.objects.filter(campaign__id=campaign_id).all()

        return [Event(id=e.id, title=e.title) for e in db_events]

    @sync_to_async
    def get_event_ids(self, campaign_id: str, first: int) -> List[str]:
        return list(
            models.Event.objects.filter(campaign__id=campaign_id).values_list(
                "id", flat=True
            )[:first]
        )

    @sync_to_async
    def get_events_batch(self, event_ids: List[str]) -> List[List[Event]]:
        return list(models.Event.objects.filter(id__in=event_ids))
