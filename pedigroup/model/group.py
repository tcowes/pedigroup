from model.exceptions.cannotBeRemovedException import CannotBeRemovedException

class Group:

    def __init__(self, name):
        self.name = name
        self.users = set()
        self.orders = list()

    def addUser(self, user):
        self.users.add(user)

    def removeUser(self, user):
        if not self.users.__contains__(user):
            raise CannotBeRemovedException("No se puede remover un usuario el cual no pertenece al grupo")
        self.users.remove(user)

    def addOrder(self, order):
        self.orders.append(order)

    def usersQuantity(self):
        return self.users.__len__()
    
    def ordersQuantity(self):
        return self.orders.__len__()