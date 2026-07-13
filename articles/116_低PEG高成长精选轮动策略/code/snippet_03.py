def initialize(context):
    """
    初始化函数：设置回测基准、滑点、手续费、全局变量与定时任务
    """
    # 设置基准指数，这里使用沪深300
    set_benchmark('000300.XSHG')
    # 使用真实价格撮合（更接近实盘）
    set_option('use_real_price', True)
    # 避免未来函数（强制不使用未来数据）
    set_option("avoid_future_data", True)
    # 过滤掉 order 系列 API 产生的比 error 级别低的 log
    log.set_level('order', 'error')
    # 设置固定滑点，假设每笔交易有 0.02 元价差
    set_slippage(FixedSlippage(0.02))
    # 设置股票交易成本
    # 买入：佣金 0.0002
    # 卖出：佣金 0.0002 + 印花税 0.001
    # 每笔最低佣金：0.01
    set_order_cost(
        OrderCost(
            close_tax=0.001,             # 卖出印花税
            open_commission=0.0002,      # 买入佣金
            close_commission=0.0002,     # 卖出佣金
            min_commission=0.01          # 最低佣金
        ),
        type='stock'
    )
    # === 全局参数初始化 ===
    g.total_stock_num = 10             # 目标最大持仓股票数量
    g.hold_list = []                   # 当前持仓股票列表
    g.buy_list = []                    # 每次调仓时的目标买入列表
    g.high_limit_list = []             # 昨日涨停且仍持仓的股票列表
    g.limit_up_list = []               # （预留变量）记录持仓中涨停的股票
    g.history_hold_list = []           # 最近一段时间内持有过的股票记录
    g.not_buy_again_list = []          # 在某段时间内不再买入的黑名单股票
    g.limit_days = 20                  # 黑名单生效天数（近期涨停不再追高的天数）
    g.is_empty_position = False        # 是否当前需要空仓（例如：4 月全月空仓）
    # === 定时任务设定 ===
    # 每个交易日开盘前运行：准备数据、信号
    run_daily(before_market_open, time='09:25', reference_security='000300.XSHG')
    # 每周一开盘后运行：核心调仓逻辑
    run_weekly(market_opened, weekday=1, time='09:30', reference_security='000300.XSHG')
    # 每个交易日尾盘前检查涨停股（防止炸板）
    run_daily(check_limit_up, time='14:40', reference_security='000300.XSHG')
    # 每个交易日尾盘清仓（如果当日被标记为需要空仓）
    run_daily(clear_account, time='14:50')
