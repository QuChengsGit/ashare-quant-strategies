def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.yesterday_HL_list = df[df['close'] == df['high_limit']].code.tolist()
    else:
        g.yesterday_HL_list = []
def get_stock_list(context):
    yesterday = context.previous_date
    initial_list = filter_all_stock2(context, get_all_securities('stock', yesterday).index.tolist())
    factor_data = get_factor_values(initial_list, g.factor_list, end_date=yesterday, count=1)
    df_jq_factor_value = pd.DataFrame({factor: factor_data[factor].iloc[:, 0] for factor in g.factor_list}, index=initial_list)
    df_jq_factor_value = data_preprocessing(df_jq_factor_value, initial_list, industry_code, yesterday)
    tar = g.model1.predict_proba(df_jq_factor_value)[:, 1]
    df_jq_factor_value['total_score'] = tar
    df_jq_factor_value = df_jq_factor_value[df_jq_factor_value['total_score'] > 0.5].sort_values(by='total_score', ascending=False)
    positive_list = df_jq_factor_value.index.tolist()[:int(0.1 * len(df_jq_factor_value))]
    df_fundamentals = get_fundamentals(query(valuation.code, valuation.circulating_market_cap, indicator.eps)
                                        .filter(valuation.code.in_(positive_list))
                                        .order_by(valuation.circulating_market_cap.asc()))
    lst = df_fundamentals[df_fundamentals['eps'] > 0].code.tolist()
    lst = filter_paused_stock(lst)
    lst = filter_limitup_stock(context, lst)
    lst = filter_limitdown_stock(context, lst)
    tensor_list = [torch.Tensor(attribute_history(i, 60, '1d').values) for i in lst]
    stacked_tensor = torch.stack(tensor_list)
    with torch.no_grad():
        output1 = g.model1(stacked_tensor)
        output2 = g.model2(stacked_tensor)
        output3 = g.model3(stacked_tensor)
        output = output1 + output2 + output3
    data = {'ID': lst, 'score': output[:, 1].squeeze().tolist()}
    df = pd.DataFrame(data).nlargest(3, 'score')
    return df['ID'].tolist()
def weekly_adjustment(context):
    if not g.no_trading_today_signal:
        target_list = get_stock_list(context)
        for stock in g.hold_list:
            if stock not in target_list and stock not in g.yesterday_HL_list:
                log.info("卖出[%s]" % (stock))
                close_position
(context.portfolio.positions[stock])
        position_count = len(context.portfolio.positions)
        value = context.portfolio.cash / (len(target_list) - position_count)
        for stock in target_list:
            if stock not in context.portfolio.positions:
                if open_position(stock, value) and len(context.portfolio.positions) == len(target_list):
                    break
