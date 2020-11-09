from typing import List, Optional

from asgiref.sync import sync_to_async
from campaigns import models

from .entities import Campaign, Event


class CampaignRepository:
    @sync_to_async
    def get_campaign_by_id(self, id: str) -> Optional[Campaign]:
        db_campaign = models.Campaign.objects.filter(id=id).first()

        if not db_campaign:
            return None

        return Campaign(id=db_campaign.id, title=db_campaign.title)

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
