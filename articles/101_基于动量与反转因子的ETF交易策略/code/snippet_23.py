# 计算ETF的Beta
def calculate_beta(context, etf):
    etf_data = attribute_history(etf, 250, '1d', ['high', 'low'])
    betas = [np.polyfit(etf_data['low'].iloc[i:i+20], etf_data['high'].iloc[i:i+20], 1)[0] for i in range(len(etf_data) - 21)]
    return np.mean(betas) - 2 * np.std(betas)

复制
