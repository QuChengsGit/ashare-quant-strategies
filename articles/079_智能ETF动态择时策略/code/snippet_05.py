def initialize(context):
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    set_option('order_volume_ratio', 0.1)
    set_benchmark('000300.XSHG')
    set_slippage(FixedSlippage(0.001))
    set_order_cost(OrderCost(close_tax=0.000, open_commission=0.00006, close_commission=0.00006, min_commission=0), type='fund')
    # 策略参数初始化
    g.dapan_threshold = 0
    g.signal = 'BUY'
    g.lag = 20
    g.decrease_days = 0 
    g.increase_days = 0 
    g.unit = '30m'
    # 主要指数列表和ETF对照表
    g.zs_list = ['000001.XSHG', '399001.XSHE', '399006.XSHE', '000852.XSHG', '000015.XSHG']
    g.ETF_list = {
        '399905.XSHE':'159902.XSHE', 
        '399632.XSHE':'159901.XSHE', 
        '000016.XSHG':'510050.XSHG', 
        '000010.XSHG':'510180.XSHG',
        '000852.XSHG':'512100.XSHG',
        '399295.XSHE':'159966.XSHE',
        '399958.XSHE':'159967.XSHE',
        '000015.XSHG':'510880.XSHG',
        '399324.XSHE':'159905.XSHE',
        '399006.XSHE':'159915.XSHE',
        '000300.XSHG':'510300.XSHG',
        '000905.XSHG':'510500.XSHG',
        '399673.XSHE':'159949.XSHE',
        '000688.XSHG':'588000.XSHG'
    }
    g.not_ipo_list = g.ETF_list.copy()
    g.available_indexs = []
    run_daily(check_etf, time='9:15')
    run_daily(check_trade, time='11:15')

复制
