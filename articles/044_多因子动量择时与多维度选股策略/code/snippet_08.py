def get_stock_list(context):
    initial_list = get_all_securities().index.tolist()
    initial_list = filter_new_stock(context, initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = filter_st_stock(initial_list)
    initial_list = filter_kcb_stock(context, initial_list)
    initial_list = growth_profit(context, initial_list)  # 净利润增长率筛选
    initial_list = peg(context, initial_list)  # PEG筛选
    initial_list = get_factor_filter_list(context, initial_list, 'TVSTD20', True, 0, 0.3)  # 20日成交金额的标准差筛选
    final_list = get_stock_rank_m_m(context, initial_list)  # 综合因子评分筛选
    return final_list

复制
