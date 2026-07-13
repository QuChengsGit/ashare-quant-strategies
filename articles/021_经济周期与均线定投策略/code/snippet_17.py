def year_move_average(year_point: list) -> float:
    year_len = len(year_point)
    if year_len >= 2:
        x = np.arange(year_len)
        params = np.polyfit(x, year_point, 1)
        return params[0] * x[-1] + params[1]
    return year_point[0]

复制
