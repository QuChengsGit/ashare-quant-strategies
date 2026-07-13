def select_stocks(composite_score, industry_mask, n=20):
    candidates = composite_score[industry_mask]
    return candidates.head(n).index.tolist()

复制
