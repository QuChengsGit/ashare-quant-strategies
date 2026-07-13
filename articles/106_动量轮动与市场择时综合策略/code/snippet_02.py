def get_stock_pool():
    # 选取热门行业概念并筛选符合条件的股票池
    concept_names = [...]
    # 获取各行业的股票代码
    all_concepts = get_concepts()
    concept_codes = [code for name in concept_names for code in all_concepts[all_concepts['name'] == name].index]
    all_concept_stocks = [get_concept_stocks(code) for code in concept_codes]
    # 查询市值范围在30亿到1000亿之间的股票
    q = query(valuation.code).filter(valuation.market_cap >= 30, valuation.market_cap <= 1000)
    stock_df = get_fundamentals(q)
    stock_pool = stock_df['code'].tolist()
    # 过滤创业板、科创板、ST股票和停牌股票
    stock_pool = filter_st_stock(filter_paused_stock(stock_pool))
    return stock_pool
