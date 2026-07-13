def initialize(context):
    # 设置日志输出级别
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    # 下单不超过成交量的10%
    set_option('order_volume_ratio', 0.1)
    # 设置回测基准
    set_benchmark('000300.XSHG')
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001,
                             open_commission=0.0003, close_commission=0.0003,
                             min_commission=5), type='stock')
    # 设置滑点
    set_slippage(FixedSlippage(0.002))
    # 全局变量定义
    g.stock_num = 20
    g.buylist = []
    g.high_limit_list = []
    # 调度计划
    run_daily(get_high_limit, time='9:00')
    run_monthly(get_stocks, 1, time='10:00')
    run_monthly(trade_stocks, 1, time='14:55')
    run_monthly(show_cap, 1, time='16:00')
    run_daily(check_high_limit, time='14:40')
