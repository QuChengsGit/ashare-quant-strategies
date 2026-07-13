def trade(context):
    target_num = 1  # 目标持仓ETF数量
    rank_df = get_rank(g.etf_pool)
    c = max(rank_df.score) - min(rank_df.score)
    # 判断是否有明确的动量信号
    if 0.1 < c < 15:
        target_list = list(rank_df.index)[:target_num]
    else:
        target_list = []
    # RSRS择时模型筛选
    real_target_list = []
    for etf in target_list:
        hl = attribute_history(etf, 18, '1d', ['high', 'low'])
        if np.polyfit(hl.low, hl.high, 1)[0] > getBeta(context, etf):
            real_target_list.append(etf)
    target_list = real_target_list
    # 卖出非目标ETF
    hold_list = list(context.portfolio.positions)
    for etf in hold_list:
        if etf not in target_list:
            order_target_value(etf, 0)
    # 买入目标ETF
    if target_list:
        hold_list = list(context.portfolio.positions)
        if len(hold_list) < target_num:
            value = context.portfolio.available_cash / (target_num - len(hold_list))
            for etf in target_list:
                if context.portfolio.positions[etf].total_amount == 0:
                    order_target_value(etf, value)
