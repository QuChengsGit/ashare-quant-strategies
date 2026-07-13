def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]  # 获取当前持仓股票
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.high_limit_list = list(df[df['close'] == df['high_limit']].code)  # 获取昨日涨停股票
    else:
        g.high_limit_list = []
def before_market_open(context):
    g.check_out_lists = []
    current_data = get_current_data()
    check_date = context.previous_date - datetime.timedelta(days=200)
    all_stocks = list(get_all_securities(date=check_date).index)
    # 筛选股票：剔除创业板、ST、停牌、涨停开盘、跌停开盘等股票
    all_stocks = [stock for stock in all_stocks if not (
            (current_data[stock].day_open == current_data[stock].high_limit) or
            (current_data[stock].day_open == current_data[stock].low_limit) or
            current_data[stock].paused or
            current_data[stock].is_st or
            ('ST' in current_data[stock].name) or
            ('*' in current_data[stock].name) or
            ('退' in current_data[stock].name) or
            (stock.startswith('30')) or  # 创业板
            (stock.startswith('68')) or  # 科创板
            (stock.startswith('8')) or  # 北交所
            (stock.startswith('4'))   # 北交所
    )]
    # 基于市值、估值和财务指标进行筛选
    q = query(
        valuation.code, valuation.market_cap, valuation.pe_ratio, income.total_operating_revenue
        ).filter(
        valuation.pb_ratio < 1,  # 市净率低于1
        cash_flow.subtotal_operate_cash_inflow > 1e6,  # 经营活动现金流入大于100万
        indicator.adjusted_profit > 1e6,  # 调整后净利润大于100万
        indicator.roa > 0.15,  # 资产回报率大于15%
        indicator.inc_net_profit_year_on_year > 0,  # 净利润同比增长为正
    	valuation.code.in_(all_stocks)
    	).order_by(
    	indicator.roa.desc()  # 按资产回报率降序排列
    ).limit(
    	g.buy_stock_count * 3
    )
    g.check_out_lists = list(get_fundamentals(q).code)[:g.buy_stock_count]
    log.info("今日股票池：%s" % g.check_out_lists)
    send_mail(context, g.check_out_lists, ["可买"] * len(g.check_out_lists), '大市值价值投资-本月筛选', '本月筛选股票')

复制
