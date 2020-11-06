from typing import List, Optional

from asgiref.sync import sync_to_async
from campaigns import models
from django.db.models import F

from .entities import Campaign, Event


class CampaignRepository:
    @sync_to_async
    def get_campaign_by_id(self, id: str) -> Optional[Campaign]:
        db_campaign = models.Campaign.objects.filter(id=id).first()

        if not db_campaign:
            return None

        return Campaign(id=db_campaign.id, title=db_campaign.title)

    @sync_to_async
    def get_campaigns(self) -> List[Campaign]:
        return List(models.Campaign.objects.all())


class EventRepository:
    @sync_to_async
    def get_events_for_campaign(self, campaign_id: str) -> List[Event]:
        db_events = models.Event.objects.filter(campaign__id=campaign_id).all()

        return [Event(id=e.id, title=e.title) for e in db_events]

    @sync_to_async
    def get_events_for_campaign_batch(
        self, campaign_ids: List[str]
    ) -> List[List[Event]]:
        db_events = (
            models.Event.objects.filter(campaign__id__in=campaign_ids)
            .all()
            .annotate(campaign_id=F("campaign__id"))
        )

        data = []

        for id in campaign_ids:
            data.append(
                [
                    Event(id=e.id, title=e.title)
                    for e in db_events
                    if e.campaign_id == id
                ]
            )

        return data
