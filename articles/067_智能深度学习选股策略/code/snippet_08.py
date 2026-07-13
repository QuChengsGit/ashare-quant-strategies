def check_limit_up(context):
    now_time = context.current_dt
    if g.yesterday_HL_list:
        for stock in g.yesterday_HL_list:
            current_data = get_price(stock, end_date=now_time, frequency='1m', fields=['close', 'high_limit'], skip_paused=False, fq='pre', count=1, panel=False, fill_paused=True)
            if current_data.iloc[0, 0] < current_data.iloc[0, 1]:
                position = context.portfolio.positions[stock]
                close_position(position)
def close_account(context):
    if g.no_trading_today_signal and g.hold_list:
        for stock in g.hold_list:
            position = context.portfolio.positions[stock]
            close_position(position)

复制
