# Generate model instances with factory-boy.

from datetime import timedelta

import factory

from web import models as _models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.User

    username = factory.Faker("user_name")


class AbteilungFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.Abteilung

    name = factory.Faker("company")
    user = factory.SubFactory(UserFactory)


class NachweisFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.Nachweis

    betrieb = factory.Faker("text")
    schule = factory.Faker("text")

    nummer = factory.Sequence(lambda n: n)
    ausbildungswoche = factory.Faker("random_int", min=1, max=200)
    jahr = factory.LazyAttribute(lambda x: x.datum_start.year)
    kalenderwoche = factory.Faker("random_int", min=1, max=52)
    datum_start = factory.Faker("date_object")
    datum_ende = factory.LazyAttribute(lambda x: x.datum_start + timedelta(days=4))
    abteilung = factory.SubFactory(AbteilungFactory)
    user = factory.SubFactory(UserFactory)
