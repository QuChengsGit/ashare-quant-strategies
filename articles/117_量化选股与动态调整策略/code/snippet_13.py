def weekly_adjustment(context):
    all_list = get_stock_list(context)
    sg_list = all_list[0][:5]
    ms_list = all_list[1][:5]
    peg_list = all_list[2][:5]
    union_list = list(set(sg_list).union(set(ms_list)).union(set(peg_list)))
    ...
    g.target_list = g.target_list[:min(g.stock_num, len(g.target_list))]  # 截取不超过最大持仓数的股票量

    # 卖出不在目标池中的股票
    for stock in g.hold_list:
        if stock not in g.target_list:
            close_position(position)
    ...

复制
