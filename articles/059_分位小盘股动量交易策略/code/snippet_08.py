def drop_outlier(data_list):
    data_list.sort()
    q1 = data_list[int(len(data_list) / 4)]
    q3 = data_list[int(len(data_list) * 3 / 4)]
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    data_list = [x for x in data_list if x >= low and x <= high]  # 去除极值
    return data_list
def divide_list_into_10(data_list):
    data_list.sort()
    chunk_size = len(data_list) // 10
    lst_of_chunks = [data_list[i:i+chunk_size] for i in range(0, len(data_list), chunk_size)]
    result_list = [min(chunk) for chunk in lst_of_chunks]  # 返回每个部分的最小值
    return result_list
def iUpdate(context):
    nchoice = 10  # 选股数量
    nposition = 5  # 持仓数量
    dt_last = context.previous_date
    all_stock = get_all_securities('stock', dt_last)
    # 过滤ST股票和部分板块股票
    cdata = get_current_data()
    stocks = [s for s in all_stock.index if not cdata[s].is_st]
    stocks = [stock for stock in stocks if not stock.startswith('8') and not stock.startswith('688') and not stock.startswith('9')]
    # 获取上一个交易日的日期和因子信息
    previous_trade_day = get_previous_trade_day(context.current_dt, 1)
    valuation_df = get_fundamentals(query(
                valuation.code,
                valuation.turnover_ratio,
                valuation.circulating_cap,
                valuation.capitalization,
                valuation.circulating_market_cap,
                indicator.roe,
                valuation.pe_ratio
            ).filter(
                valuation.code.in_(stocks)
            ), date=previous_trade_day).dropna().set_index('code')
    # 因子处理与筛选
    circulating_cap_factor_list = drop_outlier(valuation_df['circulating_cap'].tolist())
    circulating_cap_factor_list = divide_list_into_10(circulating_cap_factor_list)
    # 筛选小盘股
    df = get_fundamentals(query(
            valuation.code,
            valuation.market_cap,
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio > 0,
            valuation.circulating_cap > circulating_cap_factor_list[0],
            valuation.circulating_cap < circulating_cap_factor_list[1],
            indicator.roe > 0,
            indicator.roa > 0.45,
        ).order_by(valuation.market_cap.asc()
        ).limit(nchoice)
    ).dropna().set_index('code')
    g.choice = df.index.tolist()  # 选定的股票列表
    g.position_size = 1.0/nposition * context.portfolio.total_value  # 持仓的目标头寸大小
    print(g.choice)

复制
