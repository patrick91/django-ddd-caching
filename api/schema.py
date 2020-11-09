import asyncio
from typing import List, Optional

import strawberry
from campaigns.domain.repositories import CampaignRepository, EventRepository


@strawberry.type
class Event:
    id: strawberry.ID
    title: str


@strawberry.type
class Campaign:
    id: strawberry.ID
    title: str

    @strawberry.field
    async def events(self, info, first: int) -> List[Event]:
        repo = info.context.repositories.event_repository
        loader = info.context.loaders.event_loader

        print("fetching events ids campaign id=", self.id)
        event_ids = await repo.get_event_ids(campaign_id=self.id, first=first)

        print("fetching events", event_ids)
        events = await asyncio.gather(*(loader.load(id) for id in event_ids))

        return [Event(id=e.id, title=e.title) for e in events]


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self, info) -> str:
        return await info.context.redis.get("my-key", encoding="utf-8") or "FALLBACK"

    @strawberry.field
    async def campaign(self, info, id: strawberry.ID) -> Optional[Campaign]:
        context = info.context

        entity_campaign = (
            await context.repositories.campaign_repository.get_campaign_by_id(id)
        )

        if entity_campaign:
            return Campaign(
                id=strawberry.ID(entity_campaign.id), title=entity_campaign.title
            )

        return None

    @strawberry.field
    async def campaigns(self, info, first: int) -> List[Campaign]:
        context = info.context

        entity_campaigns = await context.repositories.campaign_repository.get_campaigns(
            first=first
        )

        return [
            Campaign(id=strawberry.ID(e.id), title=e.title) for e in entity_campaigns
        ]


schema = strawberry.Schema(Query)
