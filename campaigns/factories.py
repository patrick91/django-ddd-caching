import factory
import factory.django

from .models import Brand, Event, Campaign


class BrandFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Brand

    name = factory.Faker("name")


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    title = factory.Faker("sentence", nb_words=4)
    body = factory.Faker("text")


class CampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Campaign

    title = factory.Faker("sentence", nb_words=4)
    body = factory.Faker("text")
    brand = factory.SubFactory(BrandFactory)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        self.events.set([e.id for e in EventFactory.create_batch(5)])
