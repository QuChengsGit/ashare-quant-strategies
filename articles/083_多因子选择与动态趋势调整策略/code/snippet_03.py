def sorted_by_circulating_market_cap(stock_list, n_limit_top=5):
    q = query(
        valuation.code,
    ).filter(
        valuation.code.in_(stock_list),
        indicator.eps > 0  # 筛选每股收益大于0的股票
    ).order_by(
        valuation.circulating_market_cap.asc()  # 按流通市值升序排序
    ).limit(
        n_limit_top
    )
    return get_fundamentals(q)['code'].tolist()
