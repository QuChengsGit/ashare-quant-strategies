def transform_date(date, date_type):
    if isinstance(date, str):
        dt_date = dt.datetime.strptime(date, '%Y-%m-%d')
    elif isinstance(date, dt.datetime):
        dt_date = date
    elif isinstance(date, dt.date):
        dt_date = dt.datetime.combine(date, dt.datetime.min.time())
    else:
        raise ValueError("Invalid date format")
    date_mapping = {
        'str': dt_date.strftime('%Y-%m-%d'),
        'dt': dt_date,
        'd': dt_date.date()
    }
    return date_mapping[date_type]
def get_shifted_date(date, days, days_type='T'):
    d_date = transform_date(date, 'd')
    yesterday = d_date + dt.timedelta(-1)
    if days_type == 'N':
        shifted_date = yesterday + dt.timedelta(days + 1)
    elif days_type == 'T':
        all_trade_days = [i.strftime('%Y-%m-%d') for i in list(get_all_trade_days())]
        if str(yesterday) in all_trade_days:
            shifted_date = all_trade_days[all_trade_days.index(str(yesterday)) + days + 1]
        else:
            for i in range(100):
                last_trade_date = yesterday - dt.timedelta(i)
                if str(last_trade_date) in all_trade_days:
                    shifted_date = all_trade_days[all_trade_days.index(str(last_trade_date)) + days + 1]
                    break
    return str(shifted_date)

复制
