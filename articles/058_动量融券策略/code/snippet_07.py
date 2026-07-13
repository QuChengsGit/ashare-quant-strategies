def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    g.buylist0 = []
# 技术说明：
# 在开盘前的准备阶段，初始化当日的股票买卖列表 `g.buylist0`，为后续的交易决策做准备。

复制
