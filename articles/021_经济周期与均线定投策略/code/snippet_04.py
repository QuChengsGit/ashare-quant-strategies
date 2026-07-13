def calc_provide_and_need(start_date: str, end_date: str) -> tuple:
    end_date = calc_last_month(end_date)
    df = macro.run_query(query(
        macro.MAC_MANUFACTURING_PMI.stat_month,
        macro.MAC_MANUFACTURING_PMI.produce_idx,
        macro.MAC_MANUFACTURING_PMI.new_orders_idx
    ).filter(
        macro.MAC_MANUFACTURING_PMI.stat_month >= start_date,
        macro.MAC_MANUFACTURING_PMI.stat_month <= end_date
    ).order_by(
        macro.MAC_MANUFACTURING_PMI.stat_month.desc()
    ))
    produce_seq = np.array(df['produce_idx'])
    new_orders_seq = np.array(df['new_orders_idx'])
    produce_percent = percentile(produce_seq, df.iloc[0, 1])
    new_orders_percent = percentile(new_orders_seq, df.iloc[0, 2])
    return (produce_percent, new_orders_percent)
