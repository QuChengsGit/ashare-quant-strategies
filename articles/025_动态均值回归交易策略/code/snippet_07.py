def cancel_previous_order(order_id):
    if order_id is not None:
        orders = get_open_orders()
        for _order in orders.values():
            if _order.order_id == order_id:
                cancel_order(_order)
