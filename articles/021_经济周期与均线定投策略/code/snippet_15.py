def calc_save(start_date: str, end_date: str) -> tuple:
    end_date = calc_last_month(end_date)
    df = macro.run_query(query(
        macro.MAC_MANUFACTURING_PMI.stat_month,
        macro.MAC_MANUFACTURING_PMI.raw_material_idx,
        macro.MAC_MANUFACTURING_PMI.finished_produce_idx
    ).filter(
        macro.MAC_MANUFACTURING_PMI.stat_month >= start_date,
        macro.MAC_MANUFACTURING_PMI.stat_month <= end_date
    ).order_by(
        macro.MAC_MANUFACTURING
_PMI.stat_month.desc()
    ))
    raw_material_seq = np.array(df['raw_material_idx'])
    finished_produce_seq = np.array(df['finished_produce_idx'])
    raw_material_percent = percentile(raw_material_seq, df.iloc[0, 1])
    finished_produce_percent = percentile(finished_produce_seq, df.iloc[0, 2])
    return (raw_material_percent, finished_produce_percent)

复制
