from __future__ import annotations

from asyncio.tasks import gather
from typing import List, Optional

from asgiref.sync import sync_to_async
from campaigns import models

from domain.repositories.redis import BaseRedisRepository
from domain.repositories.stats import increase_sql_queries

from ..entities import Campaign


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
