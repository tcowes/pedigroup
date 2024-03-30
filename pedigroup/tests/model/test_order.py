import unittest
from model.order import Order
from model.group import Group
from model.empanada import Empanada

class TestOrder(unittest.TestCase):

    def setUp(self):
        group = Group("Epersonal")
        self.order = Order(group)
        self.empanada = Empanada("Carne", "Unq King")
    
    def test_an_order_is_created_without_food_to_order(self):
        self.assertEqual(self.order.totalQuantity, 0)

    def test_an_order_to_which_3_empanadas_are_added_has_3_units_of_food_to_be_ordered(self):
        self.order.addEmpanadas(self.empanada, 3)
        self.assertEqual(self.order.totalQuantity, 3)

    def test_when_trying_to_add_a_negative_quantity_of_empanadas_to_an_order_an_exception_is_triggered(self):
        with self.assertRaises(ValueError):
            self.order.addEmpanadas(self.empanada, -1)

if __name__ == '__main__':
    unittest.main()