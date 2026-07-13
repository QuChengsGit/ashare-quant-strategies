def get_PMI(date: str) -> list:
    start_date = date
    for i in range(13):
        start_date = calc_last_month(start_date)
    df = macro.run_query(query(
        macro.MAC_MANUFACTURING_PMI.pmi
    ).filter(
        macro.MAC_MANUFACTURING_PMI.stat_month >= start_date,
        macro.MAC_MANUFACTURING_PMI.stat_month < date
    ).order_by(
        macro.MAC_MANUFACTURING_PMI.stat_month.asc()
    ))
    return list(np.array(df['pmi']))

复制
