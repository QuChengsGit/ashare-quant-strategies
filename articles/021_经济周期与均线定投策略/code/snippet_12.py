def handle(context):
    pre_date = context.previous_date
    current_date = context.current_dt.strftime('%Y-%m-%d').split('-')
    current_date = datetime.date(int(current_date[0]), int(current_date[1]), int(current_date[2]))
    diff_days = (current_date - pre_date).days
    if g.mode in [0, 2]:
        current_date = current_date.strftime('%Y-%m')
        x = [0,1,2,3,4,5,6,7,8,9,10,11,12]
        y = get_PMI(current_date)
        params = op.curve_fit(func, x, y)
        k = 2 * params[0][0] * 12 + params[0][1]
        if k > 0.0 and y[-1] >= 50.0 and y[0] <= y[-1]:
            provide_and_need = calc_provide_and_need(g.begin_date, current_date)
            if provide_and_need[0] < 50.0 and provide_and_need[1] > 50.0:
                save = calc_save(g.begin_date, current_date)
                if save[0] < 50.0:
                    g.mode = 1
    if g.mode == 1:
        if g.times == -1:
            g.record = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
        if g.bond_security in context.portfolio.positions.keys():
            order_target(g.bond_security, 0)
        current_price = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
        fund_price = float(np.array(get_bars(g.stock_security, 1, '1d', fields=['close'], include_now=True, df=True))[0])
        withdraw = Decimal(str(current_price)) / Decimal(str(g.record)) - Decimal('1.0')
        if withdraw < Decimal('-0.02') or g.times == -1:
            g.times += 1
            order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
            g.record = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
        else:
            if diff_days > 2:
                order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
    if g.mode in [0, 2]:
        if g.mode == 0:
            year_point = change_to_yeak_k()
            yearMa10 = year_move_average(year_point)
            current_price = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
            fund_price = float(np.array(get_bars(g.stock_security, 1, '1d', fields=['close'], include_now=True, df=True))[0])
            if current_price < yearMa10:
                g.mode = 2
                g.record = yearMa10
                g.times += 1
                if g.bond_security in context.portfolio.positions.keys():
                    order_target(g.bond_security, 0)
                order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
        if g.mode == 2:
            current_price = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
            fund_price = float(np.array(get_bars(g.stock_security, 1, '1d', fields=['close'], include_now=True, df=True))[0])
            withdraw = Decimal(str(current_price)) / Decimal(str(g.record)) - Decimal('1.0')
            if withdraw < Decimal('-0.05'):
                g.times += 1
                order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
                g.record = float(np.array(get_bars('000300.XSHG', 1, '1d', fields=['close'], include_now=True, df=True))[0])
            else:
                if diff_days > 2:
                    order_func(context.portfolio.total_value, context.portfolio.available_cash, fund_price)
    if g.mode in [1, 2]:
        ma5 = day_move_average(5, True)
        ma10 = day_move_average(10, True)
        ma20 = day_move_average(20, True)
        ma30 = day_move_average(30, True)
        ma30_pre = day_move_average(30, False)
        if ma5 > ma10 > ma20 > ma30 > ma30_pre:
            order_value(g.stock_security, context.portfolio.available_cash)
    if g.stock_security in context.portfolio.positions.keys():
        sell_stock_security(current_date, context.portfolio.total_value, list(context.portfolio.positions.keys()))

复制
