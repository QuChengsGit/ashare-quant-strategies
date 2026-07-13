def close_account(context):
    if g.no_trading_today_signal:
        position_count = context.portfolio.positions
        if len(position_count) != 0:
            for stock in position_count:
                position = context.portfolio.positions[stock]
                close_position(position)
                log.info("卖出[%s]" % (stock))

复制
