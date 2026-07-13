def initialize(context):
    # 设置基准、真实价格、避免未来函数等系统选项
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    g.benchmark = '000905.XSHG'  # 中证500指数
    set_benchmark(g.benchmark)
    # 日志与显示格式设置
    log.set_level('order', 'error')
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.max_columns', 10)
    pd.set_option('display.width', 500)
    # 子账户资金分配
    g.stock_share = 0.7  # 股票账户占比
    g.future_share = 0.3  # 期货账户占比
    g.future_position = 0.35  # 期货账户中可用于持仓的比例
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash * g.stock_share, type='stock'),
                       SubPortfolioConfig(cash=context.portfolio.starting_cash * g.future_share, type='futures')])
    # 股票投资策略参数设置
    g.index = '399317.XSHE'  # 中证500指数成分股
    g.num = 5  # 每次选股数量
    g.stocks = []  # 当前股票池
    # 期货投资策略参数设置
    g.future_type = 'IC'  # 中证500期货
    g.futures_margin_rate = 0.15  # 期货保证金比例
    g.unitprice = 200  # 期货单位价格
    g.long_days = 5  # 开多均线天数
    g.short_days = 2  # 开空均线天数
    g.ATRdays = 20  # ATR止损参数
    g.boundrydays = 5  # 最高最低价区间长度
    g.stop = 5  # ATR止损倍数
    g.shortdays = 20  # 波动率计算短期天数
    g.longdays = 50  # 波动率计算长期天数
    g.para = 1  # 波动率调整参数
    g.day = 20  # 期货周期天数
    g.k = 1  # 期货初始交易手数
    g.day_count = g.day  # 初始化日计数
    # 期货交易相关设置
    set_order_cost(OrderCost(open_commission=0.000023, close_commission=0.000023, close_today_commission=0.0023), type='index_futures')
    set_option('futures_margin_rate', g.futures_margin_rate)
    set_slippage(StepRelatedSlippage(2))  # 期货交易滑点设置
    # 每日运行函数
    run_daily(handle_trader, time='13:45')  # 股票交易函数
    run_daily(before_market_open_future, time='9:00', reference_security='IF8888.CCFX')  # 期货开盘前准备
    run_daily(market_trade_future, time='11:15', reference_security='IF8888.CCFX')  # 期货交易函数
