from django.test import TestCase

from .models import GroupOrder, Order, Group, Product, Restaurant, User
from .exceptions import CannotBeRemovedException

class TestRestaurant(TestCase):

    def setUp(self):
        self.restaurant = Restaurant(name="Eden", address="Calle Falsa 123", phone_number="1144554455")
        self.restaurant.save()

    def test_a_restaurant_is_created_without_products(self):
        self.assertEqual(self.restaurant.products_quantity(), 0)

    def test_a_restaurant_has_a_product_after_adding_one_to_it(self):
        self.restaurant.add_product("Empanada de pollo", 250.0)
        self.assertEqual(self.restaurant.products_quantity(), 1)


class TestGroup(TestCase):

    def setUp(self):
        self.group = Group(name="Epersonal", id_app=1)
        self.group.save()
        self.user = User(first_name="Lucas", last_name="Ziegemann", 
                         username="lziege", id_app=1, is_bot=False)
        self.user.save()
    
    def test_a_group_is_created_without_users_and_orders(self):
        self.assertEqual(self.group.users_quantity(), 0)
        self.assertEqual(self.group.orders_quantity(), 0)

    def test_a_group_and_a_user_have_each_other_after_adding_this_user_to_the_group(self):
        self.group.add_user(self.user)
        self.assertEqual(self.group.users_quantity(), 1)
        self.assertEqual(self.user.groups_quantity(), 1)

    def test_a_group_and_a_user_do_not_have_each_other_after_the_user_is_removed_from_the_group(self):
        self.group.add_user(self.user)
        self.group.remove_user(self.user)
        self.assertEqual(self.group.users_quantity(), 0)
        self.assertEqual(self.user.groups_quantity(), 0)

    def test_when_trying_to_remove_a_user_from_a_group_to_which_he_does_not_belong_an_exception_is_thrown(self):
        with self.assertRaises(CannotBeRemovedException):
            self.group.remove_user(self.user)

    def test_a_group_has_a_group_order_after_one_is_created_with_this_group(self):
        self.group.place_group_order(list())
        self.assertEqual(self.group.orders_quantity(), 1)


class TestGroupOrder(TestCase):

    def setUp(self):
        group = Group(name="Epersonal", id_app=1)
        group.save()
        self.group_order = GroupOrder(group=group)
        self.group_order.save()

    def test_a_group_order_is_created_without_orders_and_an_estimated_price_of_0(self):
        self.assertEqual(self.group_order.orders_quantity(), 0)
        self.assertEqual(self.group_order.estimated_price, 0)

    def test_a_group_order_has_an_order_after_adding_one_with_its_estimated_price(self):
        restaurant = Restaurant(name="Eden", address="Calle Falsa 123", phone_number="1144554455")
        restaurant.save()
        product = Product(name="Empanada de carne", restaurant=restaurant, estimated_price=250.0)
        product.save()
        user = User(first_name="Lucas", last_name="Ziegemann", 
                    username="lziege", id_app=1, is_bot=False)
        user.save()
        order = Order(product=product, quantity=2, user=user, estimated_price=product.estimated_price)
        order.save()
        self.group_order.add_order(order)
        self.assertEqual(self.group_order.orders_quantity(), 1)
        self.assertEqual(self.group_order.estimated_price, 250.0)


class TestOrder(TestCase):

    def setUp(self):
        restaurant = Restaurant(name="Eden", address="Calle Falsa 123", phone_number="1144554455")
        restaurant.save()
        self.product = Product(name="Empanada de carne", restaurant=restaurant)
        self.product.save()
        self.user = User(first_name="Lucas", last_name="Ziegemann", 
                    username="lziege", id_app=1, is_bot=False)
        self.user.save()
        self.order = Order(product=self.product, quantity=2, user=self.user)
        self.order.save()
    
    def test_an_order_is_created_with_a_product_a_quantity_and_a_user(self):
        self.assertEqual(self.order.product, self.product)
        self.assertEqual(self.order.quantity, 2)
        self.assertEqual(self.order.user, self.user)

    def test_an_order_can_be_started_without_an_assigned_group_order(self):
        self.assertEqual(self.order.group_order, None)

    def test_an_order_has_a_group_order_after_being_added_to_it(self):
        group = Group(name="Epersonal", id_app=1)
        group.save()
        group_order = group.place_group_order(list())
        group_order.add_order(self.order)
        self.assertEqual(self.order.group_order, group_order)


class TestUser(TestCase):

    def setUp(self):
        self.user = User(first_name="Lucas", last_name="Ziegemann", 
                         username="lziege", id_app=1, is_bot=False)
        self.user.save()
        self.group = Group(name="Epersonal", id_app=1)
        self.group.save()
    
    def test_a_user_is_created_without_groups_and_orders(self):
        self.assertEqual(self.user.groups_quantity(), 0)
        self.assertEqual(self.user.orders_quantity(), 0)

    def test_a_user_and_a_group_have_each_other_after_the_user_is_added_to_the_group(self):
        self.user.join_the_group(self.group)
        self.assertEqual(self.user.groups_quantity(), 1)
        self.assertEqual(self.group.users_quantity(), 1)

    def test_a_user_and_a_group_do_not_have_each_other_after_the_user_leaves_the_group(self):
        self.user.join_the_group(self.group)
        self.user.leave_the_group(self.group)
        self.assertEqual(self.user.groups_quantity(), 0)
        self.assertEqual(self.group.users_quantity(), 0)

    def test_when_trying_to_remove_a_group_of_a_user_to_which_it_did_not_belong_an_exception_is_thrown(self):
        with self.assertRaises(CannotBeRemovedException):
            self.user.leave_the_group(self.group)

    def test_a_user_has_an_order_after_placing_one(self):
        restaurant = Restaurant(name="Eden", address="Calle Falsa 123", phone_number="1144554455")
        restaurant.save()
        product = Product(name="Empanada de carne", restaurant=restaurant)
        product.save()
        self.user.place_order(product, 2)
        self.assertEqual(self.user.orders_quantity(), 1)