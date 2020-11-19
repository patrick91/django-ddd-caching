from __future__ import annotations

from asyncio.tasks import gather
from typing import List

from asgiref.sync import sync_to_async
from campaigns import models
from domain.repositories.cache import BaseCacheRepository
from domain.repositories.stats import increase_sql_queries

from ..entities import Campaign


class CampaignRepository(BaseCacheRepository):
    model_class = models.Campaign
    entity_class = Campaign

    @increase_sql_queries
    @sync_to_async
    def _get_campaigns_ids(self, first: int) -> List[Campaign]:
        return list(self.model_class.objects.all().values_list("id", flat=True)[:first])

    async def get_campaigns(self, first: int) -> List[Campaign]:
        ids = await self._get_campaigns_ids(first)

        return await gather(*(self.get_by_id(id) for id in ids))
