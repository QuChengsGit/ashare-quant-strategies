import pandas as pd
import numpy as np

# =============================
# 1. 数据预处理与因子计算
# =============================
def compute_industry_momentum(industry_prices, window=60):
    momentum = industry_prices.pct_change(window).iloc[-1]
    return momentum.sort_values(ascending=False)

def compute_factors(stock_data):
    factors = pd.DataFrame(index=stock_data.index)
    factors["value_pe"] = 1 / stock_data["PE"]
    factors["quality_roea"] = stock_data["ROE"]
    factors["volatility"] = -stock_data["Return"].rolling(20).std()
    factors["momentum_20d"] = stock_data["Return"].rolling(20).mean()
    return factors

def standardize_factors(factors):
    zscore = (factors - factors.mean()) / factors.std()
    return zscore.fillna(0)

def compute_composite_score(factors, weights):
    score = (factors * weights).sum(axis=1)
    return score.sort_values(ascending=False)

# =============================
# 2. 行业筛选与行业内选股
# =============================
def industry_stock_filter(stock_industry_map, top_industries):
    mask = stock_industry_map.isin(top_industries)
    return mask

def select_stocks(composite_score, industry_mask, n=20):
    candidates = composite_score[industry_mask]
    return candidates.head(n).index.tolist()

# =============================
# 3. 组合构建与权重控制
# =============================
def volatility_scaling(returns, target_vol=0.15):
    realized_vol = returns.rolling(20).std().iloc[-1] * np.sqrt(252)
    scale = target_vol / realized_vol
    return min(max(scale, 0.5), 2.0)

def compute_portfolio_weights(selected_stocks):
    n = len(selected_stocks)
    return {s: 1.0 / n for s in selected_stocks}

# =============================
# 4. 执行层：交易成本与调仓逻辑
# =============================
def apply_transaction_costs(prev_weights, new_weights, cost_rate=0.001):
    turnover = sum(abs(new_weights.get(s, 0) - prev_weights.get(s, 0)) for s in set(prev_weights) | set(new_weights))
    cost = turnover * cost_rate
    return max(1 - cost, 0)

def rebalance_portfolio(daily_data, prev_weights, industry_prices, stock_industry_map, factor_weights):
    industry_mom = compute_industry_momentum(industry_prices)
    top_industries = industry_mom.index[:3]

    stock_data = daily_data
    factors = compute_factors(stock_data)
    factors_std = standardize_factors(factors)
    composite_score = compute_composite_score(factors_std, factor_weights)

    industry_mask = industry_stock_filter(stock_industry_map, top_industries)
    selected_stocks = select_stocks(composite_score, industry_mask)

    base_weights = compute_portfolio_weights(selected_stocks)

    vol_scale = volatility_scaling(stock_data["Return"])
    scaled_weights = {s: w * vol_scale for s, w in base_weights.items()}

    tcost_multiplier = apply_transaction_costs(prev_weights, scaled_weights)
    final_weights = {s: w * tcost_multiplier for s, w in scaled_weights.items()}

    return final_weights
