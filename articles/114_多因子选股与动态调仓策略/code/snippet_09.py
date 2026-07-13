def weekly_adjustment(context):
    if not g.no_trading_today_signal:
        target_list = get_stock_list(context)
        # 卖出不符合的股票
        for stock in g.hold_list:
            if stock not in target_list and stock not in g.yesterday_HL_list:
                log.info(f"卖出[{stock}]")
                position = context.portfolio.positions[stock]
                close_position(position)
            else:
                log.info(f"已持有[{stock}]")
        # 买入新的股票
        position_count = len(context.portfolio.positions)
        target_num = len(target_list)
        if target_num > position_count:
            value = context.portfolio.cash / (target_num - position_count)
            for stock in target_list:
                if context.portfolio.positions[stock].total_amount == 0:
                    if open_position(stock, value):
                        if len(context.portfolio.positions) == target_num:
                            break

复制
