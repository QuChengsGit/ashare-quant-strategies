def change_to_yeak_k() -> list:
    date = get_previous_date('2015-01', '1m')
    result = []
    while date <= get_current_date():
        df = get_bars('000300.XSHG', 1, date, fields=['close'], include_now=True, df=True)
        df = df.rename(columns={'close': date})
        result.append(float(df[date].mean()))
        date = get_previous_date(date, '1m')
    return result

复制
