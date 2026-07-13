def set_param():
    g.stocknum = 4  # 理想持股数量
    g.bearpercent = 0.3  # 熊市仓位
    g.bearposition = True  # 熊市是否持仓
    g.sellrank = 10  # 排名多少位之后(不含)卖出
    g.buyrank = 9  # 排名多少位之前(含)可以买入
    g.tradeday = 300  # 上市天数
    g.increase1d = 0.087  # 前一日涨幅
    g.tradevaluemin = 0.01  # 最小流通市值 单位（亿）
    g.tradevaluemax = 1000  # 最大流通市值 单位（亿）
    g.pbmin = 0.5  # 最小市净率
    g.pbmax = 3.5  # 最大市净率
    g.weights = [5, 5, 8, 4, 10]  # 排名条件及权重
    g.MA = ['000001.XSHG', 10]  # 均线择时
    g.choose_time_signal = True  # 启用择时信号
    g.threshold = 0.003  # 牛熊切换阈值
    g.buyagain = 5  # 再次买入的间隔时间
