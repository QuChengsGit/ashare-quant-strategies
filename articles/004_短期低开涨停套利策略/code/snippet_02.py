def buy(context):
    # 基础信息
    date = transform_date(context.previous_date, 'str')
    current_data = get_current_data()
    # 获取昨日涨停的股票
    initial_list = prepare_stock_list(date)
    hl_list = get_hl_stock(initial_list, date)
    if hl_list:
        # 获取非连板涨停的股票
        ccd = get_continue_count_df(hl_list, date, 10)
        lb_list = list(ccd.index)
        stock_list = [s for s in hl_list if s not in lb_list]
        # 计算相对位置，选择位置较低的股票
        rpd = get_relative_position_df(stock_list, date, 60)
        rpd = rpd[rpd['rp'] <= 0.5]
        stock_list = list(rpd.index)
        # 筛选出低开的股票
        if stock_list:
            df = get_price(stock_list, end_date=date, frequency='daily', fields=['close'], count=1, panel=False, fill_paused=False, skip_paused=True).set_index('code')
            df['open_pct'] = [current_data[s].day_open / df.loc[s, 'close'] for s in stock_list]
            df = df[(0.96 <= df['open_pct']) & (df['open_pct'] <= 0.97)]  # 仅选择低开3%左右的股票
            stock_list = list(df.index)
        # 买入操作
        if not context.portfolio.positions and stock_list:
            for s in stock_list:
                order_target_value(s, context.portfolio.total_value / len(stock_list))
                log.info(f"买入: {get_security_info(s, date).display_name} ({s})")
