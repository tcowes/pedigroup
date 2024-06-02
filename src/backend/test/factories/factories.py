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


class RestaurantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Restaurant


class ProductFactory(factory.django.DjangoModelFactory):
    restaurant = factory.SubFactory(RestaurantFactory)

    class Meta:
        model = Product


class OrderFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1

    class Meta:
        model = Order
