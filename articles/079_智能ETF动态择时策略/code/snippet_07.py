def get_N_trade_date(date, N, is_before=True):
    all_date = pd.Series(get_all_trade_days())
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    if isinstance(date, datetime.datetime):
        date = date.date()
    if is_before:
        return all_date[all_date <= date].tail(N).values[0]
    else:
        return all_date[all_date >= date].head(N).values[-1]

复制
