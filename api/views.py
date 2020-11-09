from dataclasses import dataclass, field
from functools import cached_property
from typing import List

import aioredis
from campaigns.domain.repositories import CampaignRepository, EventRepository
from strawberry.dataloader import DataLoader
from strawberry.django.views import AsyncGraphQLView as BaseAsyncGraphQLView


async def load_events(keys: List[str]):
    repo = EventRepository()

    print("fetching keys", keys)

    return await repo.get_events_batch(keys)


class Repositories:
    @cached_property
    def event_repository(self):
        return EventRepository()

    @cached_property
    def campaign_repository(self):
        return CampaignRepository()


class Loaders:
    @cached_property
    def event_loader(self):
        return DataLoader(load_events)


@dataclass
class Context:
    redis: aioredis.Redis

    repositories: Repositories = field(default_factory=Repositories)
    loaders: Loaders = field(default_factory=Loaders)


class AsyncGraphQLView(BaseAsyncGraphQLView):
    async def get_context(self, request):
        redis = await aioredis.create_redis_pool("redis://localhost")

        await redis.set('my-key', 'value')

        return Context(redis=redis)
