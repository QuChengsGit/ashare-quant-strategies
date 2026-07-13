def iUpdate(context):
    index = '399310.XSHE'  # 国证50指数
    n = 50  # 股票持仓数量
    rente_ratio = 0.05  # 年金利率，设定为5%
    cash_ratio = 2 * rente_ratio  # 现金储备率，设定为10%
    treasury_ratio = 0.4  # 债券仓位，设定为40%
    treasury_fund = '000012.XSHG'  # 债券基金，选择国债指数
    cur_data = get_current_data()
    # 每年年初进行分红操作和再平衡
    if context.current_dt.year > context.previous_date.year:
        rente = int(rente_ratio * context.portfolio.total_value)
        log.info('!!!分红+++', rente, int(context.portfolio.available_cash))
        inout_cash(-rente)
        if not cur_data[treasury_fund].paused:
            treasury_size = treasury_ratio * context.portfolio.total_value
            log.info('再平衡', treasury_fund)
            order_target_value(treasury_fund, treasury_size)
    stocks = get_index_stocks(index)
    # 卖出不在股票池中的股票
    for s in context.portfolio.positions:
        if s not in stocks and not cur_data[s].paused:
            log.info('sell', s, cur_data[s].name)
            order_target(s, 0)
    # 根据配置买入新的股票
    cash_size = cash_ratio * context.portfolio.total_value
    position_size = (1.0 - cash_ratio - treasury_ratio) / n * context.portfolio.total_value
    for s in stocks:
        if context.portfolio.available_cash < cash_size:
            break  # 如果现金不够，不继续买入
        if s not in context.portfolio.positions and not cur_data[s].paused:
            log.info('buy', s, cur_data[s].name)
            order_value(s, position_size)
    record(NetValue=context.portfolio.total_value / 10000)  # 记录净值，单位：万元

复制
