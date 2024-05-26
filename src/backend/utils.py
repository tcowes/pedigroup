from collections import defaultdict

from backend.models import Order


def format_order(orders: list[Order]) -> str:
    grouped_order = defaultdict(lambda: 0)
    for order in orders:
        grouped_order[order.product_name()] += order.quantity
    return "\n".join([f"{product_name}: {quantity}" for product_name, quantity in grouped_order.items()])
