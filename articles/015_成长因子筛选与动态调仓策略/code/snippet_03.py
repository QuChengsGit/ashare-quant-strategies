def my_trade(context):
    g.no_trading_today_signal = today_is_between(context, '04-05', '04-30')
    g.hold_list = list(context.portfolio.positions.keys())
    if g.no_trading_today_signal:
        return
    check_out_list = get_stock_list(context)
    check_out_list = filter_limitup_stock(context, check_out_list)
    check_out_list = filter_limitdown_stock(context, check_out_list)
    check_out_list = filter_paused_stock(check_out_list)
    check_out_list = check_out_list[:g.stock_num]
    adjust_position(context, check_out_list)
