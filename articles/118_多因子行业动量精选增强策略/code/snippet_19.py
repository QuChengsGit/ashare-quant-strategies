def volatility_scaling(returns, target_vol=0.15):
    realized_vol = returns.rolling(20).std().iloc[-1] * np.sqrt(252)
    scale = target_vol / realized_vol
    return min(max(scale, 0.5), 2.0)

复制
