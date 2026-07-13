def market_open(context):
    log.info('开始还券...')
    rq_stock = context.portfolio.short_positions
    # 还券操作
    for stock in rq_stock:
        current_price = get_bars(stock, count=1, unit='5m', fields=['close'], include_now=True)['close'][-1]
        log.info("买券还券: %s" % [stock, current_price, rq_stock[stock].total_amount])
        marginsec_close(stock, rq_stock[stock].total_amount)
# 技术说明：
# 市场开盘后，策略会首先执行还券操作，即对前一交易日融券卖出的股票进行买入并还券，以清算头寸。

复制
