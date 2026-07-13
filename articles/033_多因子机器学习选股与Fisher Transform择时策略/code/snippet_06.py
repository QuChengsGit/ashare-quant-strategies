def fisher_transform_strategy(context, security_list):
    buyable_stocks = []
    end_date = context.previous_date
    period = 10
    def fisher_transform(data, period=period):
        high = data['high']
        low = data['low']
        close = data['close']
        mid_price = (high + low) / 2.0
        typical_price = (high + low + close) / 3.0
        smoothed_price = (mid_price + typical_price) / 2.0
        price_diff = typical_price - mid_price
        abs_diff = np.abs(price_diff)
        fisher = np.log((1 + abs_diff) / (1 - abs_diff))
        return fisher
    for security in security_list:
        df = get_price(security, end_date=end_date, count=period, panel=False, fill_paused=False)
        df['fisher'] = fisher_transform(df)
        if df['fisher'].iloc[-1] > 0:
            buyable_stocks.append(security)
    return buyable_stocks
