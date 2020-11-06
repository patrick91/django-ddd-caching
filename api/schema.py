from typing import List, Optional

import strawberry
from campaigns.domain.repositories import CampaignRepository


@strawberry.type
class Event:
    id: strawberry.ID
    title: str


@strawberry.type
class Campaign:
    id: strawberry.ID
    title: str

    @strawberry.field
    async def events(self, info) -> List[Event]:
        events = await info.context["loader"].load(self.id)

        return [Event(id=e.id, title=e.title) for e in events]


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self) -> str:
        return "Hello!"

    @strawberry.field
    async def campaign(self, id: strawberry.ID) -> Optional[Campaign]:
        repo = CampaignRepository()

        entity_campaign = await repo.get_campaign_by_id(id)

        if entity_campaign:
            return Campaign(
                id=strawberry.ID(entity_campaign.id), title=entity_campaign.title
            )

        return None

    @strawberry.field
    async def campaigns(self) -> List[Campaign]:
        repo = CampaignRepository()

        entity_campaigns = await repo.get_campaigns()

        return [
            Campaign(id=strawberry.ID(e.id), title=e.title) for e in entity_campaigns
        ]


schema = strawberry.Schema(Query)
