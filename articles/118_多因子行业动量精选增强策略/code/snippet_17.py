def industry_stock_filter(stock_industry_map, top_industries):
    mask = stock_industry_map.isin(top_industries)
    return mask

复制
