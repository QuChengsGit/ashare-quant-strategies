def sell(context):
    data_today = get_current_data()
    for s in context.portfolio.positions:
        print("sell:" + s)
        order_target(s, 0)
