# Generate model instances with factory-boy.


import factory

from tests.test_web.models import AbteilungDummy, NachweisDummy


class AbteilungDummyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AbteilungDummy

    name = factory.Faker("company")


class NachweisDummyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NachweisDummy

    nummer = factory.Sequence(lambda n: n)
    abteilung = factory.SubFactory(AbteilungDummyFactory)
    fertig = factory.Faker("pybool")
    unterschrieben = factory.Faker("pybool")
