def market_open(context):
    current_data = get_current_data()
    if g.sel_stock is None:
        return
    if context.current_dt.time() >= g.strategy_starttime:
        if g.not_buy_flg == 1:
            now_buy_price = get_buy_price(context)
            cancel_previous_order(g.last_buy_orderid)
            g.last_buy_price = now_buy_price
            buy_count = int(context.portfolio.available_cash / now_buy_price / 100) * 100
            if buy_count >= 100:
                new_order = order(g.sel_stock, buy_count, LimitOrderStyle(now_buy_price))
                update_order_status(new_order, is_buy=True)
        if context.current_dt.time() < g.strategy_endtime and g.not_sell_flg == 1:
            now_sell_price = get_sell_price(context)
            cancel_previous_order(g.last_sell_orderid)
            if g.sel_stock in context.portfolio.positions and context.portfolio.positions[g.sel_stock].closeable_amount > 0:
                g.last_sell_price = now_sell_price
                new_order = order(g.sel_stock, -context.portfolio.positions[g.sel_stock].closeable_amount, LimitOrderStyle(now_sell_price))
                update_order_status(new_order, is_buy=False)
