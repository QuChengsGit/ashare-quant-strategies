# 获取ETF评分
def get_etf_scores(etf_pool, lookback_days, reversal_lookback_days):
    scores = []
    for etf in etf_pool:
        momentum_score = get_momentum_score(etf, lookback_days)
        reversal_score = get_reversal_score(etf, reversal_lookback_days)
        final_score = momentum_score - reversal_score / 6
        scores.append(final_score)
    return pd.DataFrame({'etf': etf_pool, 'score': scores}).sort_values(by='score', ascending=False)

复制
