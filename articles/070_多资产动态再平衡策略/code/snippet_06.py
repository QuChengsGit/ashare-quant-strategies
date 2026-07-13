def initialize(context):
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 使用真实价格交易
    set_option("avoid_future_data", True)  # 避免未来数据影响
    log.info('初始函数开始运行且全局只运行一次')
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置股票交易成本
    set_order_cost(OrderCost(open_commission=0.0003, close_commission=0.0003, min_commission=5), type='fund')  # 设置基金交易成本
    g.confidencelevel = 2.58  # 风险信心水平，对应99%的置信区间
    g.rebalanced_asset_values = {}
    g.raise_rate = -1  # 涨幅触发再平衡的比例，<=0不触发
    g.period = 12  # 调仓周期
    g.run_count = 0  # 跑动次数计数
    g.pool = {
        'stock': {'rate': 0.3, 'codes': [
            {'510310.XSHG': datetime.datetime(2013, 3, 25)},
            {'513100.XSHG': datetime.datetime(2013, 5, 15)},
            {'513500.XSHG': datetime.datetime(2014, 1, 15)},
        ]},
        'mid_bond': {'rate': 0.15, 'codes': [{'511010.XSHG': datetime.datetime(2013, 3, 25)}]},
        'long_bond': {'rate': 0.4, 'codes': [{'511260.XSHG': datetime.datetime(2017, 8, 24)}]},  # 10年期国债
        'gold': {'rate': 0.075, 'codes': [{'518880.XSHG': datetime.datetime(2013, 7, 29)}]},
        'goods': {'rate': 0.075, 'codes': [{'510170.XSHG': datetime.datetime(2011, 1, 25)}]},
    }
    g.stock_map_asset = init_stock_map_asset(g.pool)  # 初始化股票与资产类别的映射关系
    run_monthly(market_open, monthday=1, time='open', reference_security='000001.XSHG')  # 每月初进行再平衡

复制
