def before_market_open(context):
    g.is_empty_position = today_is_between(context, '04-01', '04-30')  # 判断4月空仓信号
    get_history_hold_list(context)  # 获取历史持仓列表
    get_yesterday_limit_up_stocks(context)  # 获取昨日涨停列表

复制
