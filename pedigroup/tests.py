import unittest
from model.user import User

class TestUser(unittest.TestCase):
    
    def test_un_usuario_es_creado_sin_grupos(self):
        usuario = User("Lucas", "lziege")
        self.assertEqual(usuario.groups.__len__(), 0)

    def test_un_usuario_tiene_un_grupo_luego_de_añadirsele_uno(self):
        usuario = User("Lucas", "lziege")
        usuario.addGroup("pedigroup")
        self.assertEqual(usuario.groups.__len__(), 1)
    
if __name__ == '__main__':
    unittest.main()