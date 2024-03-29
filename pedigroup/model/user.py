from model.exceptions.cannotBeRemovedException import CannotBeRemovedException

class User:

    def __init__(self, first_name, last_name, username, phone, id_app):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.phone = phone
        self.id_app = id_app
        self.groups = set()

    def addGroup(self, group):
        self.groups.add(group)

    def removeGroup(self, group):
        if not self.groups.__contains__(group):
            raise CannotBeRemovedException("No se puede remover un grupo al cual un usuario no pertenece")
        self.groups.remove(group)

    def groupsQuantity(self):
        return self.groups.__len__()