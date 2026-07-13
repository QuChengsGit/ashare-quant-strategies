def initialize(context):
    run_type = context.run_params.type
    log.info('开始 {} 交易.'.format(run_type))
    set_benchmark('000002.XSHG')  # 设置沪深300为基准
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 打开防未来数据选项
    set_slippage(FixedSlippage(0))  # 设置滑点为0
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.00012,\
                close_commission=0.0003, close_today_commission=0, min_commission=5),\
                type='fund')  # 设置交易费用
    log.set_level('order', 'error')  # 设置日志级别为error，减少不必要的信息输出
    g.strat_name = ''  # 策略名称，用于保存持仓列表
    g.yesterday_list = []  # 上一交易日持仓
    g.stock_list = []  # 今天的持股
    g.limit_price = [1, 100]  # 股价限制
    # 每日的定时任务
    run_daily(before_market_open, time='8:30', reference_security='000300.XSHG')
    run_daily(market_open, time='9:35', reference_security='000300.XSHG')
