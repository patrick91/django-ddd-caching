import asyncio
from typing import List, Optional

import strawberry
from campaigns.domain import entities

from .extensions import ApolloTracingExtension


@strawberry.type
class Brand:
    id: strawberry.ID
    name: str

    @classmethod
    def from_entity(cls, entity: entities.Brand):
        return cls(
            id=strawberry.ID(entity.id),
            name=entity.name,
        )


@strawberry.type
class Event:
    id: strawberry.ID
    title: str
    body: str

    @classmethod
    def from_entity(cls, entity: entities.Event):
        return cls(
            id=strawberry.ID(entity.id),
            title=entity.title,
            body=entity.body,
        )


@strawberry.type
class Campaign:
    id: strawberry.ID
    title: str
    body: str
    brand_id: strawberry.Private[str]

    @classmethod
    def from_entity(cls, entity: entities.Campaign):
        return cls(
            id=strawberry.ID(entity.id),
            brand_id=entity.brand_id,
            title=entity.title,
            body=entity.body,
        )

    @strawberry.field
    async def brand(self, info) -> Brand:
        return await info.context.loaders.brand_loader.load(self.brand_id)

    @strawberry.field
    async def events(self, info, first: int) -> List[Event]:
        repo = info.context.repositories.event_repository
        loader = info.context.loaders.event_loader

        print("fetching events ids campaign id=", self.id)
        event_ids = await repo.get_event_ids(campaign_id=self.id, first=first)

        print("fetching events", event_ids)
        events = await asyncio.gather(*(loader.load(id) for id in event_ids))

        return [Event.from_entity(e) for e in events]


@strawberry.type
class Query:
    @strawberry.field
    async def campaign(self, info, id: strawberry.ID) -> Optional[Campaign]:
        context = info.context

        campaign_entity = (
            await context.repositories.campaign_repository.get_campaign_by_id(id)
        )

        if campaign_entity:
            return Campaign.from_entity(campaign_entity)

        return None

    @strawberry.field
    async def campaigns(self, info, first: int) -> List[Campaign]:
        context = info.context

        campaign_entities = (
            await context.repositories.campaign_repository.get_campaigns(first=first)
        )

        return [Campaign.from_entity(e) for e in campaign_entities]


schema = strawberry.Schema(Query, extensions=[ApolloTracingExtension])
