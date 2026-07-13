def transform_date(date, date_type):
    if type(date) == str:
        dt_date = dt.datetime.strptime(date, '%Y-%m-%d')
    elif type(date) == dt.datetime:
        dt_date = date
    elif type(date) == dt.date:
        dt_date = dt.datetime(date.year, date.month, date.day)
    return {'str': dt_date.strftime('%Y-%m-%d'), 'dt': dt_date, 'd': dt_date.date()}[date_type]
def get_shifted_date(date, days, days_type='T'):
    d_date = transform_date(date, 'd')
    yesterday = d_date - dt.timedelta(days=1)
    if days_type == 'T':
        trade_days = [i.strftime('%Y-%m-%d') for i in list(get_all_trade_days())]
        last_trade_date = next(d for d in trade_days if d < str(yesterday))
        shifted_date = trade_days[trade_days.index(last_trade_date) + days]
    return shifted_date
