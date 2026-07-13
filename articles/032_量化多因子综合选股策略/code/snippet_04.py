def mysell(context):
    g.chosen_stock_list = get_stock_rank_m_m(g.chosen_stock_list)
    my_adjust_position(context, g.chosen_stock_list)
