def set_params():
    g.index = '000905.XSHG'  # 股票池基准指数
    g.pool_filter = 'R'  # 涨幅过滤选项
    g.strategy = 'T'  # 策略选择：T代表趋势策略
    g.fields_name = 'close'  # 选股时使用的价格字段
    g.short_duration = 20  # 短期趋势周期
    g.trend_up = 999  # 趋势斜率上限
    g.trend_down = 0  # 趋势斜率下限
    g.lostcontrol = 2  # 动态止损类型
    g.drop_line = 0.75  # 动态止损回撤线
    g.drop_ma_days = 20  # 动态止损均线周期

复制
