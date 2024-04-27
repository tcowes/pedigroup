from .exceptions import CannotBeRemovedException
from django.db import models

class Restaurant(models.Model):
    name = models.CharField(max_length=30)
    address = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15)

    def add_product(self, product_name: str, estimated_price: float):
        product = Product(name=product_name, restaurant=self, estimated_price=estimated_price)
        product.save()

    def products_quantity(self):
        return self.products.count()


class Product(models.Model):
    name = models.CharField(max_length=30)
    restaurant = models.ForeignKey(Restaurant, related_name='products', on_delete=models.CASCADE)
    estimated_price = models.FloatField(default=0)


class Group(models.Model):
    name = models.CharField(max_length=30)
    id_app = models.BigIntegerField()

    def add_user(self, user: 'User'):
        self.users.add(user)

    def remove_user(self, user: 'User'):
        if not self.users.filter(id_app=user.id_app).exists():
            raise CannotBeRemovedException("No se puede remover un usuario el cual no pertenece al grupo")
        self.users.remove(user)

    def place_group_order(self, orders: list['Order']):
        group_order = GroupOrder(group=self)
        group_order.save()
        for order in orders:
            group_order.add_order(order)
        return group_order

    def users_quantity(self):
        return self.users.count()
    
    def orders_quantity(self):
        return self.group_orders.count()


class GroupOrder(models.Model):
    estimated_price = models.FloatField(default=0)
    group = models.ForeignKey(Group, related_name='group_orders', on_delete=models.CASCADE)

    def add_order(self, order: 'Order'):
        self.orders.add(order)
        self.estimated_price += order.estimated_price

    def orders_quantity(self):
        return self.orders.count()


class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    estimated_price = models.FloatField(default=0)
    user = models.ForeignKey("User", related_name='orders', on_delete=models.CASCADE)
    group_order = models.ForeignKey(GroupOrder, related_name='orders', on_delete=models.CASCADE, null=True)


class User(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=30)
    id_app = models.BigIntegerField()
    groups = models.ManyToManyField(Group, related_name='users')
    is_bot = models.BooleanField()

    def join_the_group(self, group: Group):
        self.groups.add(group)

    def leave_the_group(self, group: Group):
        if not self.groups.filter(id_app=group.id_app).exists():
            raise CannotBeRemovedException("No se puede remover un grupo al cual un usuario no pertenece")
        self.groups.remove(group)

    def place_order(self, product: Product, quantity: int):
        estimated_order_price = product.estimated_price * quantity
        order = Order(product=product, quantity=quantity, user=self, estimated_price=estimated_order_price)
        order.save()
        return order

    def groups_quantity(self):
        return self.groups.count()
    
    def orders_quantity(self):
        return self.orders.count()