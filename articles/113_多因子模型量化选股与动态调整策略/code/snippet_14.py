def prepare_stock_list(context):
    # 获取已持仓列表
    g.hold_list = list(context.portfolio.positions)
    # 获取历史持仓列表
    g.history_hold_list.append(g.hold_list)
    if len(g.history_hold_list) >= g.limit_days:
        g.history_hold_list = g.history_hold_list[-g.limit_days:]
    temp_set = set()
    for hold_list in g.history_hold_list:
        temp_set = temp_set.union(set(hold_list))
    g.not_buy_again_list = list(temp_set)

复制
