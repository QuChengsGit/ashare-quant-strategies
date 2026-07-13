def getBeta(context, etf):
    beta_dict = {
        '518880.XSHG': countBeta(context, '518880.XSHG'),  # 黄金ETF
        '513100.XSHG': countBeta(context, '513100.XSHG'),  # 纳指100ETF
        '159915.XSHE': countBeta(context, '159915.XSHE'),  # 创业板100ETF
        '510180.XSHG': countBeta(context, '510180.XSHG')   # 上证180ETF
    }
    return beta_dict.get(etf, 0)
def countBeta(context, etf):
    etf_data = attribute_history(etf, 250, '1d', fields=['high', 'low'])
    beta_list = []
    for i in range(len(etf_data) - 21):
        df = etf_data.iloc[i:i+20]
        beta_list.append(np.polyfit(df.low, df.high, 1)[0])
    return np.mean(beta_list) - 2 * np.std(beta_list)

复制
