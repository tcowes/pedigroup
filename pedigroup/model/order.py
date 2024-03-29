class Order:

    def __init__(self, group):
        self.group = group
        self.pastys = list()
        self.totalQuantity = 0

    def addPastys(self, pasty, quantity):
        if quantity < 0:
            raise ValueError("La cantidad a añadir no puede ser negativa")
        count: int = quantity
        while count != 0:
            self.pastys.append(pasty)
            self.totalQuantity += 1
            count -= 1