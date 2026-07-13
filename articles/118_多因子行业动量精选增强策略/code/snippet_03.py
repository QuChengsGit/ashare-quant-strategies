def compute_factors(stock_data):
    factors = pd.DataFrame(index=stock_data.index)
    factors["value_pe"] = 1 / stock_data["PE"]
    factors["quality_roea"] = stock_data["ROE"]
    factors["volatility"] = -stock_data["Return"].rolling(20).std()
    factors["momentum_20d"] = stock_data["Return"].rolling(20).mean()
    return factors
