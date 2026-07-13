def adjust_position_buy(context, buy_stocks):
    position_count = len(context.portfolio.positions)
    if g.stock_num >= position_count:
        for stock in buy_stocks:
            psize = context.portfolio.total_value * 2 / (g.stock_num + 4 + buy_stocks.index(stock))
            G = get_bars(stock, 1, '1d', ['high', 'low', 'open', 'close'], end_dt=context.current_dt, include_now=True)
            r = np.mean(list(G[0]))
            H = get_bars(stock, 50, '1d', ['high', 'low', 'open', 'close'], end_dt=context.current_dt, include_now=True)
            j = [np.mean(list(a)) for a in H]
            p = (r - np.mean(j)) / np.std(j)
            if context.portfolio.available_cash < psize:
                break
            if stock not in context.portfolio.positions:
                if p < -2:
                    log.info('短期超卖，多买点: ' + str(stock))
                    order_target_value(stock, 1.5 * psize)
                elif p > 2:
                    log.info('短期超买，少买点: ' + str(stock))
                    order_target_value(stock, 0.5 * psize)
                else:
                    order_value(stock, psize)
                if len(context.portfolio.positions) == g.stock_num:
                    break
