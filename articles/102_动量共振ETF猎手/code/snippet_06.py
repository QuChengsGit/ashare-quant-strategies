def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    set_slippage(FixedSlippage(0.004))
    set_option("avoid_future_data", True)
    set_option('use_real_price', True)
    log.info('初始函数开始运行且全局只运行一次')
    set_order_cost(OrderCost(close_tax=0.00, open_commission=0.00015, close_commission=0.00015, min_commission=5), type='fund')
    run_daily(make_sure_etf_ipo, time='9:15')
    run_weekly(market_buy, weekday=3, time='11:15')
    g.dapan_threshold = 0
    g.signal = 'BUY'
    g.niu_signal = 1
    g.position = 1
    g.lag1 = 20
    g.decrease_days = 0
    g.increase_days = 0
    g.unit = '30m'
    g.bond = '511880.XSHG'
    g.zs_list = [
        '000001.XSHG', '399001.XSHE', '000300.XSHG', '000905.XSHG', '000852.XSHG', '399006.XSHE', '000688.XSHG'
    ]
    g.ETF_list = {
        '000986.XSHG': '515220.XSHG', '000827.XSHG': '516070.XSHG', '399967.XSHE': '512660.XSHG', '000995.XSHG': '159611.XSHE',
        '000987.XSHG': '159944.XSHE', '000813.XSHG': '516120.XSHG', '000989.XSHG': '159928.XSHE', '399997.XSHE': '512690.XSHG',
        '000991.XSHG': '512170.XSHG', '399971.XSHE': '512980.XSHG', '399986.XSHE': '512800.XSHG', '399975.XSHE': '159841.XSHE',
        '000993.XSHG': '512480.XSHG', '000922.XSHG': '515080.XSHG', '399440.XSHE': '515210.XSHG', '399814.XSHE': '159825.XSHE',
        '399995.XSHE': '516970.XSHG'
    }
    g.not_ipo_list = g.ETF_list.copy()
    g.available_indexs = []

复制
