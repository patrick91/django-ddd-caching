from typing import List

from strawberry.dataloader import DataLoader
from strawberry.django.views import AsyncGraphQLView as BaseAsyncGraphQLView
from campaigns.domain.repositories import EventRepository


async def load_events_for_campaigns(keys: List[List[str]]):
    repo = EventRepository()

    return await repo.get_events_for_campaign_batch(keys)


class AsyncGraphQLView(BaseAsyncGraphQLView):
    async def get_context(self, request):
        loader = DataLoader(load_events_for_campaigns)

        return {"loader": loader}
