def before_market_open(context):
    """
    开盘前运行：判断是否需要空仓、记录历史持仓、获取昨日涨停持仓股
    """
    # 判断 4 月是否需要空仓（4 月 1 日 ~ 4 月 30 日）
    g.is_empty_position = today_is_between(context, '04-01', '04-30')
    # 获取最近一段时间的历史持仓列表，并更新黑名单
    get_history_hold_list(context)
    # 获取昨日涨停的持仓股列表
    get_yesterday_limit_up_stocks(context)

复制
