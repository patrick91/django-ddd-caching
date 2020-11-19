from django.core.management.base import BaseCommand

from campaigns.factories import CampaignFactory


class Command(BaseCommand):
    help = "Seeds the database."

    def handle(self, *args, **options):
        CampaignFactory.create_batch(500)
