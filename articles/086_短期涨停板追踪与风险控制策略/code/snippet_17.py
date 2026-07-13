def day_report(context):
    current_returns=100*context.portfolio.returns
    log.info("当前收益：%.2f%%; 当前持仓数量: %s", current_returns, len(list(context.portfolio.positions.keys())))
    for s in context.portfolio.positions:
        cost=context.portfolio.positions[s].avg_cost
        price=context.portfolio.positions[s].price
        syl=(price/cost-1)*100
        log.info("    名称: %s,代码: %s,数量: %s,成本: %s,收益: %.2f%%",current_data[s].name,s,context.portfolio.positions[s].closeable_amount,context.subportfolios[0].long_positions[s].hold_cost,syl)
    log.info("总资产: {},当前收益：{}".format(context.portfolio.total_value,round(current_returns,2)))
def clean
_st_688(stocks):
    curr_data=get_current_data()
    stocks=[s for s in stocks if not (curr_data[s].is_st or('ST' in curr_data[s].name) or('*' in curr_data[s].name) or('退' in curr_data[s].name) or(s.startswith('688')))]
    return stocks

复制
