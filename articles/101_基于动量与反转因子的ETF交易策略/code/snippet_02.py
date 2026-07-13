def initialize(context):
    # 设定基准
    set_benchmark('513100.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    # 设置滑点
    set_slippage(FixedSlippage(0.002))
    # 设置交易成本
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0002, close_commission=0.0002, close_today_commission=0, min_commission=5), type='fund')
    # 过滤一定级别的日志
    log.set_level('system', 'error')
    # 参数
    g.etf_pool = [
        '518880.XSHG',  # 黄金ETF（大宗商品）
        '513100.XSHG',  # 纳指100（海外资产）
        '159915.XSHE',  # 创业板100（成长股，科技股，中小盘）
        '510180.XSHG',  # 上证180（价值股，蓝筹股，中大盘）
    ]
    g.m_days = 25  # 动量参考天数
    g.stop_loss_pct = 0.05  # 止损比例，5%
    run_daily(trade, '9:30')  # 每天运行确保即时捕捉动量变化
