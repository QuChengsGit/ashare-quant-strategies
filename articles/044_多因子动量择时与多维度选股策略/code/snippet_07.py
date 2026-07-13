def initialize(context):
    set_benchmark('399101.XSHE')  # 设定中证创新100指数为基准
    set_option('use_real_price', True)  # 使用真实价格进行交易
    set_option("avoid_future_data", True)  # 避免未来函数
    set_slippage(FixedSlippage(0))  # 设置滑点为0，假设无滑点影响
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='fund')
    log.set_level('order', 'error')  # 过滤低于error级别的日志
    # 选股参数
    g.stock_num = 4  # 最大持仓股票数
    g.ref_stock = '000300.XSHG'  # 用于择时的大盘指数
    g.N = 18  # 动量择时计算的天数
    g.M = 600  # 动量择时中RSRS指标的窗口长度
    g.score_threshold = 0.7  # 动量择时的RSRS得分阈值
    g.mean_day = 30  # 移动平均线天数
    g.mean_diff_day = 2  # 移动平均线计算的额外天数
    g.slope_series = initial_slope_series()[:-1]  # 动量择时斜率序列初始化
    g.weights = [3, 9, 8, 4, 10]  # 选股因子的权重设置
    g.sellrank = 10  # 排名超过此值的股票将被卖出
    g.buyrank = 9  # 排名在此值以内的股票可以买入
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(print_trade_info, time='15:30', reference_security='000300.XSHG')

复制
