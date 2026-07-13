def fun_initialize(context):
    g.equity = ['510300.XSHG']  # 股票类资产（以沪深300ETF为例）
    g.commodities = ['518880.XSHG']  # 商品类资产（以黄金ETF为例）
    g.bonds = ['511010.XSHG']  # 债券类资产（以上证国债ETF为例）
    g.money_fund = ['513100.XSHG']  # 货币基金（以国泰纳斯达克100ETF为例）
    g.confidence_level = 2.58  # 置信水平，用于计算ES
    g.pools = g.equity + g.commodities + g.bonds + g.money_fund
    # 统计交易资料
    for stock in g.pools:
        if stock not in g.transactionRecord:
            g.QuantLib.fun_createTransactionRecord(context, stock)
