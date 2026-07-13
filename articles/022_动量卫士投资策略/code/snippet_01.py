def initialize(context):
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_benchmark('000905.XSHG')
    set_slippage(PriceRelatedSlippage(0.000))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.0001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    g.stock_num = 10
    g.buylist = []
    g.new_high_value = context.portfolio.starting_cash
    g.maxdown = 0
    g.new_high_value = 0
    run_daily(get_high_limit_stocks, time='9:05', reference_security='000300.XSHG')
    run_monthly(select_stocks_and_buy, 1, time='9:30')
    run_daily(sell_stocks_opened_from_up_limit, time='14:00')
    run_daily(sell_hi_vol_stocks_at_dayend_and_buy_again, time='14:30')
    run_monthly(analyze_stocks_held, 1, time='15:01')
