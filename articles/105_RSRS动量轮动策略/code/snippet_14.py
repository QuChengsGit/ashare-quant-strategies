def calculate(context):
    g.check_out_list = get_rank(context, g.stock_pool)
    g.timing_signal = get_timing_signal(context, g.check_out_list)
    print("今天选股：", g.check_out_list)
    print("今天信号：", g.timing_signal)

复制
