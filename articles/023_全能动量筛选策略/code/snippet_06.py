def check_remain_amount(context):
    g.hold_list= []
    for position in list(context.portfolio.positions.values()):
        stock = position.security
        g.hold_list.append(stock)
    if len(g.hold_list) < g.stock_num:
        target_list = g.target_list
        target_list = filter_not_buy_again(target_list)
        target_list = target_list[:min(g.stock_num, len(target_list))]
        buy_security(context,target_list)
