from collections import defaultdict
from typing import Tuple

from backend.models import Order, GroupOrder


def format_order(orders: list[Order]) -> Tuple[str, int]:
    grouped_order = defaultdict(lambda: 0)
    total_quantity = 0
    for order in orders:
        grouped_order[order.product_name()] += order.quantity
        total_quantity += order.quantity
    return "\n".join([f"\t • {prod_name}: {n}" for prod_name, n in grouped_order.items()]), total_quantity


def format_group_orders_with_date(orders: list[GroupOrder], **filter_criteria) -> str:
    """Precondición: el listado de pedidos debe venir con al menos un elemento, y ordenado por fecha de pedido
    (de mas reciente a mas antigüo)."""
    return "\n\n".join(
        [f"El {order.created_at.strftime("%d/%m/%Y")} se pidió:\n{format_order(order.orders.filter(**filter_criteria))[0]}"
         for order in orders])
