import unittest
from model.user import User
from model.exceptions.cannotBeRemovedException import CannotBeRemovedException

class TestUser(unittest.TestCase):

    def setUp(self):
        self.usuario = User("Lucas", "Ziegemann", "lziege", 1147454554, 1)
    
    def test_un_usuario_es_creado_sin_grupos(self):
        self.assertEqual(self.usuario.groups.__len__(), 0)

    def test_un_usuario_tiene_un_grupo_luego_de_añadirsele_uno(self):
        self.usuario.addGroup("pedigroup")
        self.assertEqual(self.usuario.groups.__len__(), 1)

    def test_un_usuario_no_tiene_grupos_luego_de_eliminar_uno_al_que_fue_añadido_previamente(self):
        self.usuario.addGroup("pedigroup")
        self.assertEqual(self.usuario.groups.__len__(), 1)
        self.usuario.removeGroup("pedigroup")
        self.assertEqual(self.usuario.groups.__len__(), 0)

    def test_al_intentar_eliminar_un_grupo_de_un_usuario_al_cual_no_pertenecia_se_lanza_excepcion(self):
        with self.assertRaises(CannotBeRemovedException):
            self.usuario.removeGroup("pedigroup")
    
if __name__ == '__main__':
    unittest.main()