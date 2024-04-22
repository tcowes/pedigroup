from .exceptions import CannotBeRemovedException
from django.contrib.postgres.fields import ArrayField
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=30)
    restaurant = models.CharField(max_length=30)


class Group(models.Model):
    name = models.CharField(max_length=30)
    users = models.ManyToManyField("User")
    id_app = models.BigIntegerField()
    orders = models.ManyToManyField("Order")

    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        if user not in self.users.all():
            raise CannotBeRemovedException("No se puede remover un usuario el cual no pertenece al grupo")
        self.users.remove(user)

    def add_order(self, order):
        self.orders.add(order)

    def users_quantity(self):
        return self.users.count()
    
    def orders_quantity(self):
        return self.orders.count()


class Order(models.Model):
    products = models.ManyToManyField(Product)
    quantities = ArrayField(models.IntegerField(), default=list)
    totalQuantity = models.BigIntegerField(default=0)

    def add_products(self, product, quantity):
        if quantity <= 0:
            raise ValueError("La cantidad a añadir no puede ser menor a 1")
        self.products.add(product)
        self.quantities.append(quantity)
        self.totalQuantity += quantity
        self.save()


class User(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=30)
    id_app = models.BigIntegerField()
    groups = models.ManyToManyField(Group)
    orders = models.ManyToManyField(Order)

    def add_group(self, group):
        self.groups.add(group)

    def remove_group(self, group):
        if group not in self.groups.all():
            raise CannotBeRemovedException("No se puede remover un grupo al cual un usuario no pertenece")
        self.groups.remove(group)

    def add_order(self, order):
        self.orders.add(order)

    def groups_quantity(self):
        return self.groups.count()