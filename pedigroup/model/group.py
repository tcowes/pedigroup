from pedigroup.model.exceptions.cannot_be_removed_exception import CannotBeRemovedException

class Group:

    def __init__(self, name):
        self.name = name
        self.users = set()
        self.orders = list()

    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        if user not in self.users:
            raise CannotBeRemovedException("No se puede remover un usuario el cual no pertenece al grupo")
        self.users.remove(user)

    def add_order(self, order):
        self.orders.append(order)

    def users_quantity(self):
        return len(self.users)
    
    def orders_quantity(self):
        return len(self.orders)