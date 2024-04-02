from pedigroup.model.exceptions.cannot_be_removed_exception import CannotBeRemovedException

class User:

    def __init__(self, first_name, last_name, username, phone, id_app):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.phone = phone
        self.id_app = id_app
        self.groups = set()

    def add_group(self, group):
        self.groups.add(group)

    def remove_group(self, group):
        if group not in self.groups:
            raise CannotBeRemovedException("No se puede remover un grupo al cual un usuario no pertenece")
        self.groups.remove(group)

    def groups_quantity(self):
        return len(self.groups)