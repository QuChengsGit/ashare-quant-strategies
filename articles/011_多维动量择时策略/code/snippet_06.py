def my_trade_prepare(context):
    g.check_out_list = get_rank(context, g.stock_pool)
    g.timing_signal = get_timing_signal(context, g.ref_stock)
    log.info('今日自选及择时信号:{} {}'.format(g.check_out_list[0], g.timing_signal))
    cur_stock = g.check_out_list[0]
    cur_adr = g.check_out_list[2]
    change_rate = g.stock_motion[cur_stock][-1] - g.stock_motion[cur_stock][-2]
    if change_rate > g.Motion_1diff or cur_adr > g.raiser_thr:
        g.timing_signal = 'SELL'
        log.info("由于涨跌:{}%, 动量变化:{}，今日空仓".format(cur_adr, change_rate))
