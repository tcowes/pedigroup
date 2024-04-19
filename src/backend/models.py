from .exceptions import CannotBeRemovedException
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=30)
    restaurant = models.CharField(max_length=30)


class Group:

    def __init__(self, name):
        self.name = name
        self.users = set()
        self.orders = list()

    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        if user not in self.users:
            raise CannotBeRemovedException("No se puede remover un usuario el cual no pertenece al grupo")
        self.users.remove(user)

    def add_order(self, order):
        self.orders.append(order)

    def users_quantity(self):
        return len(self.users)
    
    def orders_quantity(self):
        return len(self.orders)


class Order:

    def __init__(self, group):
        self.group = group
        self.products = list()
        self.totalQuantity = 0

    def add_products(self, product, quantity):
        if quantity < 0:
            raise ValueError("La cantidad a añadir no puede ser negativa")
        for i in range(0, quantity):
            self.products.append(product)
        self.totalQuantity += quantity


class User(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=30)
    phone = models.BigIntegerField()
    id_app = models.BigIntegerField()
    groups = set()

    def add_group(self, group):
        self.groups.add(group)

    def remove_group(self, group):
        if group not in self.groups:
            raise CannotBeRemovedException("No se puede remover un grupo al cual un usuario no pertenece")
        self.groups.remove(group)

    def groups_quantity(self):
        return len(self.groups)