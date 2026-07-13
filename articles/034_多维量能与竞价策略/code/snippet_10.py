def set_params():
    g.index = 'all'  # 指数基准：all-所有股票
    g.auction_open_highlimit = 0.985  # 竞价开盘上限
    g.auction_open_lowlimit = 0.945   # 竞价开盘下限
    g.profit_line = 1.05  # 止盈门槛
    g.volume_control = 2   # 量能控制模式
    g.volume_period = 20   # 放量控制周期
    g.volume_ratio = 5     # 放量控制比例
    g.sell_mode = 0        # 持仓量能过滤模式
    g.sell_vol_period = 120  # 持仓放量控制周期
    g.sell_vol_ratio = 0.9  # 持仓放量控制比例

复制
