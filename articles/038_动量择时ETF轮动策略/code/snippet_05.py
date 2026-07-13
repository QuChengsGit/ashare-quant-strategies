def initialize(context):
    set_benchmark('513100.XSHG')  # 设置基准为纳指100 ETF
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 打开防未来数据保护
    set_slippage(FixedSlippage(0.002))  # 设置滑点为固定值
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0002, close_commission=0.0002, close_today_commission=0, min_commission=5), type='fund')  # 设置交易成本
    log.set_level('system', 'error')  # 过滤掉一定级别的日志
    # ETF池
    g.etf_pool = [
        '518880.XSHG',  # 黄金ETF（大宗商品）
        '513100.XSHG',  # 纳指100ETF（海外资产）
        '159915.XSHE',  # 创业板100ETF（成长股）
        '510180.XSHG',  # 上证180ETF（价值股）
    ]
    g.m_days = 25  # 动量参考天数
    # 每天运行交易函数
    run_daily(trade, '9:30')

复制
