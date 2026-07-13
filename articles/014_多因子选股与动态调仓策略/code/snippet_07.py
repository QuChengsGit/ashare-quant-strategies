def my_Trader(context):
    dt_last = context.previous_date
    stocks = get_all_securities('stock', dt_last).index.tolist()
    stocks = filter_kcbj_stock(stocks)
    choice = filter_st_stock(stocks)
    choice = filter_paused_stock(choice)
    choice = filter_new_stock(context, choice)
    choice = filter_limitup_stock(context, choice)
    choice = filter_limitdown_stock(context, choice)
    choice = filter_highprice_stock(context, choice)
    choice = get_peg(context, choice)
    recent_limit_up_list = get_recent_limit_up_stock(context, choice, g.limit_days)
    black_list = list(set(g.not_buy_again_list).intersection(set(recent_limit_up_list)))
    target_list = [stock for stock in choice if stock not in black_list]
    choice = target_list[:min(g.stock_num, len(target_list))]
    g.choice = choice[:g.stock_num]

复制
