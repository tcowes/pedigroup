import csv
from typing import List, Tuple, Union, TextIO

from telegram import User as TelegramUser, Chat
from django.db import transaction

from backend.constants import HEADERS_FROM_CSV, GROUP_DIDNT_ORDER_YET_MESSAGE, USER_DIDNT_ORDER_YET_MESSAGE
from backend.exceptions import WrongHeadersForCsv
from backend.models import Product, Restaurant, Group, User, GroupOrder, Order
from backend.utils import format_group_orders_with_date


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


def register_group_and_user_if_required(chat: Chat, user_app: TelegramUser):
    group, _ = Group.objects.get_or_create(id_app=chat.id, name=chat.title)
    register_user_and_add_to_group_if_required(user_app, group.id_app)


def register_user_and_add_to_group_if_required(user_app: TelegramUser, group_id: int):
    user, _ = User.objects.get_or_create(first_name=user_app.first_name, last_name=user_app.last_name,
                                         username=user_app.username, id_app=user_app.id, is_bot=user_app.is_bot)
    group = Group.objects.get(id_app=group_id)
    group.add_user(user)


def register_user_order(product: Product, quantity: int, user: TelegramUser):
    pedigroup_user = User.objects.get(id_app=user.id)
    return pedigroup_user.place_order(product, quantity)


def register_group_order(group_id: int, user_orders: List[Order]) -> GroupOrder:
    group = Group.objects.get(id_app=group_id)
    return group.place_group_order(user_orders)  # TODO: si user_orders es vacía, no habría que crear nada... PED-44


def get_last_five_orders_from_group_as_string(group_id: int) -> str:
    last_five_orders = Group.objects.get(id_app=group_id).group_orders.all().order_by('-created_at')[:5]
    if not last_five_orders:
        return GROUP_DIDNT_ORDER_YET_MESSAGE
    else:
        return format_group_orders_with_date(last_five_orders)


def get_last_five_orders_from_user_in_group_as_string(user_id: int, group_id: int) -> str:
    last_five_orders = (
        GroupOrder.objects
        .filter(group__id_app=group_id).filter(orders__user__id_app=user_id)
        .order_by('-created_at').distinct()[:5]
    )
    if not last_five_orders:
        return USER_DIDNT_ORDER_YET_MESSAGE
    else:
        return format_group_orders_with_date(last_five_orders, user__id_app=user_id)


def get_user_groups(user_id: int) -> List[Group]:
    return Group.objects.filter(users__id_app=user_id)


def get_group(group_id):
    return Group.objects.get(id_app=group_id)


def get_product(product_id):
    return Product.objects.get(id=product_id)


def get_restaurant(restaurant_id):
    return Restaurant.objects.get(id=restaurant_id)


def get_paginated_products_by_restaurant(restaurant_id, first_item, last_item):
    return Product.objects.filter(restaurant__id=restaurant_id)[first_item:last_item]


def get_paginated_restaurants_by_group(group_id, first_item, last_item):
    return Restaurant.objects.filter(group__id_app=group_id)[first_item:last_item]


def count_restaurants_for_group(group_id):
    return Restaurant.objects.filter(group__id_app=group_id).count()
