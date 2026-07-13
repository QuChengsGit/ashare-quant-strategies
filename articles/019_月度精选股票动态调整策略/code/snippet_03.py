def handle_data(context, data):
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    # 每月首次执行选股
    if context.current_dt.month != g.month and hour == 9 and minute == 30:
        my_Trader(context)
        g.month = context.current_dt.month
    # 每天下午检查涨停股票
    if hour == 14 and minute == 0:
        check_limit_up(context)
    # 显示可用现金占总资产的百分比
    record(cash=context.portfolio.available_cash / context.portfolio.total_value * 100)
