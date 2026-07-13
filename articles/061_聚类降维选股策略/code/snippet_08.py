# 获取一只股票的名称和行业信息
def get_stock_name(code):
    return get_security_info(code).display_name
def get_stock_industry(code):
    return get_industry(code, date=None)['jq_l2']['industry_name']
LIST = []
industry = []
name = []
for i in center_sample_indices:
    LIST.append(stockList[i])
    industry.append(get_industry(stockList[i], date=_end_date)[stockList[i]]['jq_l2']['industry_name'])
    name.append(get_security_info(stockList[i]).display_name)
# 获取市值和盈利能力作为最终筛选条件
q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(
    valuation.code.in_(LIST)).order_by(valuation.circulating_market_cap.asc())
df = get_fundamentals(q)
df['name'] = name
df['industry'] = industry
print(df)

复制
