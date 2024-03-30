import unittest
from model.user import User
from model.group import Group
from model.exceptions.cannotBeRemovedException import CannotBeRemovedException

class TestUser(unittest.TestCase):

    def setUp(self):
        self.user = User("Lucas", "Ziegemann", "lziege", 1147454554, 1)
        self.group = Group("Epersonal")
    
    def test_a_user_is_created_without_groups(self):
        self.assertEqual(self.user.groupsQuantity(), 0)

    def test_a_user_has_a_group_after_adding_one_to_it(self):
        self.user.addGroup(self.group)
        self.assertEqual(self.user.groupsQuantity(), 1)

    def test_a_user_has_no_groups_after_deleting_one_that_was_added_previously(self):
        self.user.addGroup(self.group)
        self.assertEqual(self.user.groupsQuantity(), 1)
        self.user.removeGroup(self.group)
        self.assertEqual(self.user.groupsQuantity(), 0)

    def test_when_trying_to_remove_a_group_of_a_user_to_which_it_did_not_belong_an_exception_is_thrown(self):
        with self.assertRaises(CannotBeRemovedException):
            self.user.removeGroup(self.group)
    
if __name__ == '__main__':
    unittest.main()