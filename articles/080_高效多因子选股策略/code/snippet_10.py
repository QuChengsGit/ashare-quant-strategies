def get_black_list(context):
    # 检查当前时间是否在特定日期范围内
    def today_is_between(context, start_date, end_date):
        today = context.current_dt.strftime('%m-%d')
        return start_date <= today <= end_date
    # 获取黑名单股票列表
    def predict_st_stocks(stock_list, stat_date, fqd):
        tmp = []
        for stock in stock_list:
            try:
                df = get_history_fundamentals(stock, fields=[income.net_profit, indicator.adjusted_profit], watch_date=stat_date, count=11, interval='1q')
                df = df.set_index('statDate')
                y1 = sum(df.loc[fqd[0]][income.net_profit])
                y2 = sum(df.loc[fqd[1]][income.net_profit])
                y3 = sum(df.loc[fqd[2]][income.net_profit])
                if min(y1, y2, y3) < 0:
                    tmp.append(stock)
            except:
                pass
        return tmp
    # 获取黑名单股票
    if today_is_between(context, '11-01', '12-31'):
        sd = context.current_dt.strftime('%Y-%m-%d')[:4] + '-11-01'
        df = get_all_securities(types=['stock'], date=sd)
        stock_list = list(df.index)
        stock_list = filter_kcbj_stock(stock_list)
        stock_list = filter_new_stock(context, stock_list, 500)
        fiscal_quarter_date_list = get_fiscal_quarters(sd)
        g.black_list = predict_st_stocks(stock_list, sd, fiscal_quarter_date_list)

复制
