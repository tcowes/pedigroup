import random

import factory

from backend.models import Group, User, Order, Product, Restaurant


class GroupFactory(factory.django.DjangoModelFactory):
    name = "Test group"
    id_app = factory.LazyAttribute(lambda x: random.randint(1, 100))

    class Meta:
        model = Group


class UserFactory(factory.django.DjangoModelFactory):
    id_app = factory.LazyAttribute(lambda x: random.randint(1, 100))
    is_bot = False

    class Meta:
        model = User


class OrderFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Order


class RestaurantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Restaurant


class ProductFactory(factory.django.DjangoModelFactory):
    restaurant = factory.SubFactory(RestaurantFactory)

    class Meta:
        model = Product
