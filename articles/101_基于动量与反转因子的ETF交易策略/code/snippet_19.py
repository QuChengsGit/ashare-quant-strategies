# 交易函数
def trade(context):
    target_num = 1
    rank_df = get_etf_scores(g.etf_pool, g.m_days, g.m_days * 8)
    # 检查评分差距
    score_diff = rank_df['score'].max() - rank_df['score'].min()
    target_list = rank_df['etf'].iloc[:target_num].tolist() if 0.1 < score_diff < 15 else []
    # RSRS择时
    target_list = [etf for etf in target_list if is_above_beta(context, etf)]
    # 卖出不在目标列表中的ETF
    for etf in context.portfolio.positions:
        if etf not in target_list:
            order_target_value(etf, 0)
        else:
            # 检查是否需要止损
            if check_stop_loss(context, etf):
                order_target_value(etf, 0)
    # 买入新的ETF
    if target_list:
        cash_per_etf = context.portfolio.available_cash / len(target_list)
        for etf in target_list:
            if context.portfolio.positions[etf].total_amount == 0:
                order_target_value(etf, cash_per_etf)

复制
