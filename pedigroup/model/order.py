class Order:

    def __init__(self, group):
        self.group = group
        self.empanadas = list()
        self.totalQuantity = 0

    def add_empanadas(self, empanada, quantity):
        if quantity < 0:
            raise ValueError("La cantidad a añadir no puede ser negativa")
        for i in range(1, quantity):
            self.empanadas.append(empanada)
        self.totalQuantity += quantity