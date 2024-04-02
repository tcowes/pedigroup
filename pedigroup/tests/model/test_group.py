import unittest
from model.group import Group
from model.user import User
from model.order import Order
from pedigroup.model.exceptions.cannot_be_removed_exception import CannotBeRemovedException

class TestGroup(unittest.TestCase):

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

if __name__ == '__main__':
    unittest.main()