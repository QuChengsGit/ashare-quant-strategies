def update_order_status(order, is_buy):
    if order is not None:
        if str(order.status) == 'held':
            g.not_sell_flg = 0 if is_buy else 1
        else:
            if is_buy:
                g.last_buy_orderid = order.order_id
            else:
                g.last_sell_orderid = order.order_id
