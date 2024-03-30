import unittest
from model.order import Order
from model.group import Group
from model.empanada import Empanada

class TestOrder(unittest.TestCase):

    def setUp(self):
        group = Group("Epersonal")
        self.order = Order(group)
        self.empanada = Empanada("Carne", "Unq King")
    
    def test_un_pedido_es_creado_sin_comida_a_pedir(self):
        self.assertEqual(self.order.totalQuantity, 0)

    def test_un_pedido_al_cual_se_le_añaden_3_empanadas_tiene_3_cantidades_de_comida_a_pedir(self):
        self.order.addEmpanadas(self.empanada, 3)
        self.assertEqual(self.order.totalQuantity, 3)

    def test_al_intentar_añadir_una_cantidad_negativa_de_empanadas_a_un_pedido_se_lanza_excepcion(self):
        with self.assertRaises(ValueError):
            self.order.addEmpanadas(self.empanada, -1)

if __name__ == '__main__':
    unittest.main()