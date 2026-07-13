def initialize(context):
    log.set_level('order', 'error')  # 设定日志输出等级
    set_option('use_real_price', True)  # 设定使用真实价格
    set_option('avoid_future_data', True)  # 防止未来函数
    set_benchmark('000905.XSHG')  # 设置基准为中证500
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    # 初始化全局变量
    g.no_trading_today_signal = False  # 是否为资金再平衡日
    g.stock_num = 5  # 持仓股票数量
    g.choice = []  # 选股池
    g.just_sold = []  # 本月已卖出的股票
    # 调度交易运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_daily(check_limit_up, time='14:00') 
    run_monthly(my_Trader, 1, time='9:30', force=True) 
    run_monthly(go_Trader, 1, time='14:55', force=True) 
    run_daily(close_account, '14:30')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
