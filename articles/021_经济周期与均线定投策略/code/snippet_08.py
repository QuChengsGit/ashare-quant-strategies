def day_move_average(day: int, is_today: bool) -> float:
    df = get_bars(g.stock_security, day, '1d', fields=['close'], include_now=is_today, df=True)
    return np.mean(df['close'])
