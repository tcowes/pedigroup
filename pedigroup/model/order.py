class Order:

    def __init__(self, group):
        self.group = group
        self.empanadas = list()
        self.totalQuantity = 0

    def addEmpanadas(self, empanada, quantity):
        if quantity < 0:
            raise ValueError("La cantidad a añadir no puede ser negativa")
        count: int = quantity
        while count != 0:
            self.empanadas.append(empanada)
            self.totalQuantity += 1
            count -= 1