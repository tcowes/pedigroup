from collections import defaultdict

from backend.models import Order, GroupOrder


def format_order(orders: list[Order]) -> str:
    grouped_order = defaultdict(lambda: 0)
    for order in orders:
        grouped_order[order.product_name()] += order.quantity
    return "\n".join([f"\t • {product_name}: {quantity}" for product_name, quantity in grouped_order.items()])


def format_group_orders_with_date(orders: list[GroupOrder], **filter_criteria) -> str:
    """Precondición: el listado de pedidos debe venir con al menos un elemento, y ordenado por fecha de pedido
    (de mas reciente a mas antigüo)."""
    return "\n\n".join(
        [f"El {order.created_at.strftime("%d/%m/%Y")} se pidió:\n{format_order(order.orders.filter(**filter_criteria))}"
         for order in orders])
