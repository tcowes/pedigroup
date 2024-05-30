import csv
from typing import List, Tuple, Union, TextIO, Dict

from telegram import User as TelegramUser, Chat
from django.db import transaction

from backend.constants import HEADERS_FROM_CSV
from backend.exceptions import WrongHeadersForCsv
from backend.models import Product, Restaurant, Group, User, GroupOrder, Order


def create_entities_through_csv(csv_file: Union[TextIO, str], group_id: int) -> Tuple[int, int, int]:
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
    csv_data = csv_file.split("\r\n") if isinstance(csv_file, str) else csv_file
    reader = csv.DictReader(csv_data, delimiter=",") 

    if reader.fieldnames != HEADERS_FROM_CSV:
        raise WrongHeadersForCsv

    group = Group.objects.get(id_app=group_id)

    with transaction.atomic():
        for row in reader:
            if not row["Restaurant"] or not row["Product"] or len(row) != 3:
                omitted_rows += 1
                continue

            # TODO: esto es optimizable, podríamos intentar crear en cascada pero Django no lo permite tan directamente
            restaurant, created = Restaurant.objects.get_or_create(name=row["Restaurant"].title(), group_id=group.id)
            if created:
                created_restaurants += 1
            
            price = float(row["Price"]) if row["Price"] else 0.0
            product = Product(name=row["Product"].title(), estimated_price=price, restaurant=restaurant)
            products_to_create.append(product)
            created_products += 1

        Product.objects.bulk_create(products_to_create)
    
    return created_restaurants, created_products, omitted_rows


def register_group_and_user_if_required(group: Chat, user_app: TelegramUser):
    if not Group.objects.filter(id_app__contains=group.id).exists():
        Group.objects.create(name=group.title, id_app=group.id)
    register_user_and_add_to_group_if_required(user_app, group.id)


def register_user_and_add_to_group_if_required(user_app: TelegramUser, group_id: int):
    user, _ = User.objects.get_or_create(first_name=user_app.first_name, last_name=user_app.last_name,
                                         username=user_app.username, id_app=user_app.id, is_bot=user_app.is_bot)
    group = Group.objects.get(id_app=group_id)
    group.add_user(user)


def register_user_order(product: Product, quantity: int, user: TelegramUser):
    pedigroup_user = User.objects.get(id_app=user.id)
    return pedigroup_user.place_order(product, quantity)


def register_group_order(pedigroup_group: Group, user_orders: List[Order]):
    group_order = GroupOrder.objects.create(group=pedigroup_group)
    for user_order in user_orders:
        group_order.add_order(user_order)
    return group_order
