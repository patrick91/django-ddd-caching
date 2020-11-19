import dataclasses
from dataclasses import dataclass
from functools import cached_property
from typing import List

import aioredis
from campaigns.domain.repositories.campaign import CampaignRepository
from campaigns.domain.repositories.event import EventRepository
from django.http.request import HttpRequest
from domain.repositories.stats import DataFetchingStats
from strawberry.dataloader import DataLoader
from strawberry.django.views import AsyncGraphQLView as BaseAsyncGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types.execution import ExecutionResult


class Repositories:
    def __init__(
        self, redis: aioredis.Redis, data_fetching_stats: DataFetchingStats
    ) -> None:
        self.redis = redis
        self.data_fetching_stats = data_fetching_stats

    @cached_property
    def event_repository(self):
        return EventRepository(self.redis, self.data_fetching_stats)

    @cached_property
    def campaign_repository(self):
        return CampaignRepository(self.redis, self.data_fetching_stats)


@dataclass
class Loaders:
    repositories: Repositories

    async def load_events(self, keys: List[str]):
        repo = self.repositories.event_repository

        print("fetching keys", keys)

        return await repo.get_events_batch(keys)

    @cached_property
    def event_loader(self):
        return DataLoader(self.load_events)


@dataclass
class Context:
    redis: aioredis.Redis

    repositories: Repositories
    loaders: Loaders


class AsyncGraphQLView(BaseAsyncGraphQLView):
    async def get_context(self, request):
        self.data_fetching_stats = DataFetchingStats()

        redis = await aioredis.create_redis_pool("redis://localhost")

        await redis.set("my-key", "value")

        repositories = Repositories(redis, self.data_fetching_stats)
        loaders = Loaders(repositories)

        return Context(redis=redis, repositories=repositories, loaders=loaders)

    async def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data = await super().process_result(request, result)

        data["extensions"] = {  # type: ignore
            "dataFetching": dataclasses.asdict(self.data_fetching_stats),
            **result.extensions,  # type: ignore
        }

        return data
