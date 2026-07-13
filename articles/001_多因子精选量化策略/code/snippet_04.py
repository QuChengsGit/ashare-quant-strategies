def weekly_adjustment(context):
    if not g.no_trading_today_signal:
        target_list = get_stock_list(context)
        # 卖出不符合条件的股票
        for stock in g.hold_list:
            if stock not in target_list and stock not in g.yesterday_HL_list:
                close_position(context.portfolio.positions[stock])
                log.info(f"卖出[{stock}]")
        # 买入新股票
        position_count = len(context.portfolio.positions)
        if len(target_list) > position_count:
            value_per_stock = context.portfolio.cash / (len(target_list) - position_count)
            for stock in target_list:
                if context.portfolio.positions[stock].total_amount == 0:
                    open_position(stock, value_per_stock)
                    if len(context.portfolio.positions) == len(target_list):
                        break
