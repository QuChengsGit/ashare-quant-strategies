def initialize(context):
    set_benchmark('000905.XSHG')  # 设定基准指数为中证500
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option('avoid_future_data', True)  # 防止未来数据泄露
    set_slippage(PriceRelatedSlippage(0.000))  # 设置理想情况下的滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.0001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('order', 'error')  # 设置日志级别为error
    g.stock_num = 10  # 持仓股票数量
    g.buylist = []  # 买入列表
    # 定时任务设置
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')  # 准备股票池
    run_monthly(my_Trader, 1, time='9:30')  # 执行交易策略
    run_daily(check_limit_up, time='14:00')  # 检查并处理昨日涨停股票
    run_daily(check_at_dayend, time='14:30')  # 尾盘检查与交易调整
