from typing import List

from strawberry.dataloader import DataLoader
from strawberry.django.views import AsyncGraphQLView as BaseAsyncGraphQLView
from campaigns.domain.repositories import EventRepository


async def load_events(keys: List[str]):
    repo = EventRepository()

    print("fetching keys", keys)

    return await repo.get_events_batch(keys)


class AsyncGraphQLView(BaseAsyncGraphQLView):
    async def get_context(self, request):
        event_loader = DataLoader(load_events)

        return {"event_loader": event_loader}
