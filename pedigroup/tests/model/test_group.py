import unittest
from model.group import Group
from model.user import User
from model.exceptions.cannotBeRemovedException import CannotBeRemovedException

class TestGroup(unittest.TestCase):

    def setUp(self):
        self.group = Group("Epersonal")
        self.usuario = User("Lucas", "Ziegemann", "lziege", 1147454554, 1)
    
    def test_un_grupo_es_creado_sin_usuarios_y_sin_pedidos(self):
        self.assertEqual(self.group.usersQuantity(), 0)
        self.assertEqual(self.group.ordersQuantity(), 0)

    def test_un_grupo_tiene_un_usuario_luego_de_añadirsele_uno(self):
        self.group.addUser(self.usuario)
        self.assertEqual(self.group.usersQuantity(), 1)

    def test_un_grupo_no_tiene_usuarios_luego_de_eliminar_uno_que_fue_añadido_previamente(self):
        self.group.addUser(self.usuario)
        self.assertEqual(self.group.usersQuantity(), 1)
        self.group.removeUser(self.usuario)
        self.assertEqual(self.group.usersQuantity(), 0)

    def test_al_intentar_eliminar_un_usuario_de_un_grupo_al_cual_no_pertenecia_se_lanza_excepcion(self):
        with self.assertRaises(CannotBeRemovedException):
            self.group.removeUser(self.usuario)

if __name__ == '__main__':
    unittest.main()