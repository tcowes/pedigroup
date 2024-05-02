import csv
from io import TextIOWrapper
from typing import List, Tuple

from django.db import transaction
from backend.exceptions import WrongHeadersForCsv
from backend.models import Product, Restaurant

HEADERS_FROM_CSV = ["Restaurant", "Product", "Price"]


def create_entities_through_csv(csv_file: TextIOWrapper) -> Tuple[int, int, int]:
    """
    Esperamos que el csv respete el siguiente formato:
    
    Restaurant,Product,Price
    Eden,Empanada de Humita,1200.00

    Caso contrario se raisea WrongHeadersForCsv.

    Además, se retorna una tupla indicando:
    - Cantidad de restaurantes creados
    - Cantidad de productos creados
    - Cantidad de filas que se omitieron
    """
    created_restaurants = 0
    created_products = 0
    omitted_rows = 0
    products_to_create: List[Product] = []
    reader = csv.DictReader(csv_file, delimiter=",")

    if reader.fieldnames != HEADERS_FROM_CSV:
       raise WrongHeadersForCsv
    
    with transaction.atomic():
        for row in reader:
            if not row["Restaurant"] or not row["Product"] or len(row) != 3:
                omitted_rows += 1
                continue

            # TODO: esto es optimizable, podríamos intentar crear en cascada pero Django no lo permite tan directamente
            restaurant, created = Restaurant.objects.get_or_create(name=row["Restaurant"])
            if created:
                created_restaurants += 1
            
            price = float(row["Price"]) if row["Price"] else 0.0
            product = Product(name=row["Product"], estimated_price=price, restaurant=restaurant)
            products_to_create.append(product)
            created_products += 1

        Product.objects.bulk_create(products_to_create)
    
    return created_restaurants, created_products, omitted_rows
