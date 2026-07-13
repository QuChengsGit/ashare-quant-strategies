def get_previous_trade_day(current_date, n):
    trade_day = get_trade_days(end_date=current_date, count=n+1)[0]  # 获取距离当前日期 `n` 天前的交易日
    return trade_day

复制
