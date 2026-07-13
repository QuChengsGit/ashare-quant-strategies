# 每周准备股票池
def weekly_prepare_stock(context):
    candidate_list = []
    yes_day = context.previous_date
    df = get_industries(name='sw_l2', date=yes_day)  # 获取申万二级行业的股票分类
    df['score'] = -100000
    df['nums'] = 0
    drop_index = []
    for industry_index in df.index:
        check_out_lists = get_industry_stocks(industry_index, yes_day)
        df.loc[industry_index, 'nums'] = len(check_out_lists)
        if len(check_out_lists) >= 20:
            score = stock_sector_score(check_out_lists, 10)  # 计算行业得分
            df.loc[industry_index, 'score'] = score
        else:
            drop_index.append(industry_index)
    df = df.drop(drop_index).sort_values(by=['score'], ascending=False)
    industry_indexs = df.index[:5]  # 选择得分最高的5个行业
    for industry_index in industry_indexs:
        if df.loc[industry_index, 'score'] > 500:
            check_out_lists = get_industry_stocks(industry_index, yes_day)
            candidate_list.extend(check_out_lists)
    candidate_list = list(set(candidate_list))
    candidate_list = filter_new_stock(context, candidate_list)
    candidate_list = filter_kcbj_stock(candidate_list)
    candidate_list = filter_st_stock(candidate_list)
    candidate_list = filter_paused_stock(candidate_list)
    candidate_list = find_strong_stock(context, candidate_list)
    g.candidate_list = candidate_list[:min(g.stock_num + 10, len(candidate_list))]
    log.info("一周准备的股票LIST %0d,如下:" % len(g.candidate_list))
    log.info(g.candidate_list)
# 每日准备股票池
def prepare_stock_list(context):
    g.hold_list = [position.security for position in context.portfolio.positions.values()]
    if g.hold_list:
        df = get_price(g.hold_list, end_date=context.previous_date, frequency='daily',
                       fields=['close', 'high_limit'], count=1, panel=False, fill_paused=False)
        g.yesterday_HL_list = list(df[df['close'] == df['high_limit']].code)
    else:
        g.yesterday_HL_list = []
    g.buy1_stock_lists = []
    g.buy2_stock_lists = []
    candidate_list = find_strong_stock(context, g.candidate_list)
    candidate_list = candidate_list[:min(g.stock_num * 2, len(candidate_list))]
    for stock in candidate_list:
        dt = attribute_history(stock, 1, '1d', ['close', 'pre_close', 'open'])
        if (dt.close[-1] > dt.pre_close[-1] * 1.01 and dt.close[-1] > dt.open[-1] and
                context.current_data[stock].day_open < dt.close[-1] * 0.97):
            g.buy1_stock_lists.append(stock)
        else:
            g.buy2_stock_lists.append(stock)
    log.info("早上待买入的股票:", g.buy1_stock_lists)
    log.info("中午待买入的股票:", g.buy2_stock_lists)
