def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 使用真实价格交易
    set_option('use_real_price', True)
    # 避免未来数据
    set_option("avoid_future_data", True)
    # 设置日志级别为error
    log.set_level('order', 'error')
    # 设置固定滑点
    set_slippage(FixedSlippage(0.002))
    # 设置交易费用
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 初始化全局变量
    g.counter = 0
    g.arg_rsquared_min = 0.8  # OLS的R方最小值，用于判断全天均匀上涨
    g.arg_close_rate = 0.052  # 收盘价涨幅下限
    g.arg_volume_days = 5  # 成交量回看天数
    g.arg_volume_multi = 2  # 成交量大于days均值的倍数
    g.arg_buy_max = 10  # 持仓股票的最大数目
    g.buy_min_ratio = 0.4  # 买入时要达到的比例
    g.arg_hold_max = 20  # 单只股票持仓时间上限
    g.hold_days = g.arg_hold_max - 1  # 初始化持仓日数记录
    g.stocks = []  # 股票池
    g.choice = 1000  # 初选股票数量
    g.etf = "518880.XSHG"  # 黄金ETF代码
    g.hold_list = []  # 当前持仓的全部股票
    g.yesterday_HL_list = []  # 记录持仓中昨日涨停的股票
    # 运行函数
    run_daily(before_market_open, time='before_open')
    run_daily(trade, time='14:55')
    run_daily(check_limit_up, time='14:00', reference_security='000852.XSHG')

复制
