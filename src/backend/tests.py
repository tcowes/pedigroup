from venv import logger
from django.test import TestCase

from .models import Order, Group, Product, User
from .exceptions import CannotBeRemovedException

class TestGroup(TestCase):

    def setUp(self):
        self.group = Group("Epersonal")
        self.user = User("Lucas", "Ziegemann", "lziege", 1147454554, 1)
    
    def test_a_group_is_created_without_users_and_orders(self):
        self.assertEqual(self.group.users_quantity(), 0)
        self.assertEqual(self.group.orders_quantity(), 0)

    def test_a_group_has_a_user_after_adding_one_to_it(self):
        self.group.add_user(self.user)
        self.assertEqual(self.group.users_quantity(), 1)

    def test_a_group_has_no_users_after_deleting_one_that_was_added_previously(self):
        self.group.add_user(self.user)
        self.assertEqual(self.group.users_quantity(), 1)
        self.group.remove_user(self.user)
        self.assertEqual(self.group.users_quantity(), 0)

    def test_when_trying_to_remove_a_user_from_a_group_to_which_he_does_not_belong_an_exception_is_thrown(self):
        with self.assertRaises(CannotBeRemovedException):
            self.group.remove_user(self.user)

    def test_a_group_has_an_order_after_adding_one_to_it(self):
        order = Order(self.group)
        self.group.add_order(order)
        self.assertEqual(self.group.orders_quantity(), 1)


class TestOrder(TestCase):

    def setUp(self):
        group = Group("Epersonal")
        self.order = Order(group)
        self.product = Product(name="Empanada de carne", restaurant="Unq King")
    
    def test_an_order_is_created_without_food_to_order(self):
        self.assertEqual(self.order.totalQuantity, 0)

    def test_an_order_to_which_3_products_are_added_has_3_units_of_food_to_be_ordered(self):
        self.order.add_products(self.product, 3)
        self.assertEqual(self.order.totalQuantity, 3)

    def test_when_trying_to_add_a_negative_quantity_of_products_to_an_order_an_exception_is_triggered(self):
        with self.assertRaises(ValueError):
            self.order.add_products(self.product, -1)


class TestUser(TestCase):

    def setUp(self):
        self.user = User(first_name="Lucas", last_name="Ziegemann", 
                         username="lziege", phone=1147454554, id_app=1)
        self.group = Group("Epersonal")
    
    def test_a_user_is_created_without_groups(self):
        self.assertEqual(self.user.groups_quantity(), 0)

    def test_a_user_has_a_group_after_adding_one_to_it(self):
        self.user.add_group(self.group)
        self.assertEqual(self.user.groups_quantity(), 1)
        self.user.groups.pop()

    def test_a_user_has_no_groups_after_deleting_one_that_was_added_previously(self):
        self.user.add_group(self.group)
        self.assertEqual(self.user.groups_quantity(), 1)
        self.user.remove_group(self.group)
        self.assertEqual(self.user.groups_quantity(), 0)

    def test_when_trying_to_remove_a_group_of_a_user_to_which_it_did_not_belong_an_exception_is_thrown(self):
        with self.assertRaises(CannotBeRemovedException):
            self.user.remove_group(self.group)