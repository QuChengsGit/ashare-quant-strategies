def after_market_close(context):
    now = context.current_dt.date()
    if str(now) in dict_position:
        g.wait_list = dict_position[str(now)]
    else:
        g.wait_list = []
    print(g.wait_list)

复制
