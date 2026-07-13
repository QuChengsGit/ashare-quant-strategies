def initialize(context):
    # 设定基准
    set_benchmark('000300.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 将滑点设置为0
    set_slippage(FixedSlippage(0))
    # 设置交易成本万分之三，不同滑点影响可在归因分析中查看
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5),type='stock')
    # 过滤order中低于error级别的日志
    log.set_level('order', 'error')
    # 初始化全局变量
    g.stock_num = 10
    g.hold_list = [] # 当前持仓的全部股票    
    g.target_list = []
    g.yesterday_HL_list = [] # 记录持仓中昨日涨停的股票
    g.not_buy_again = []
    g.factor_list = [
        'price_no_fq', # 技术指标因子 不复权价格因子
        'total_profit_to_cost_ratio', # 质量类因子 成本费用利润率
        'inventory_turnover_rate' # 质量类因子 存货周转率
    ]
    # 设置交易运行时间
    run_daily(prepare_stock_list, time='9:05', reference_security='000300.XSHG')
    run_weekly(weekly_adjustment, 1, time='9:30', reference_security='000300.XSHG')
    run_daily(trade_morning,time='9:26',reference_security='000300.XSHG')
    run_daily(trade_afternoon, time='13:00', reference_security='000300.XSHG')
