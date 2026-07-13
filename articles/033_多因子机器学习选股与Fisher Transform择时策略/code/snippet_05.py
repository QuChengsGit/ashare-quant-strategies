def getStockPrice(stock, interval):
    h = attribute_history(stock, interval, unit='1d', fields=('close'), skip_paused=True)
    return (h['close'].values[0], h['close'].values[-1])
def df_neutralization(df, X):
    for key in df.keys():
        if key != 'code' and key != X:
            y = df[key]
            x = df[X]
            df[key] = linres(y, x)
    return df
def linreg(x, y):
    x = sm.add_constant(np.array(x))
    y = np.array(y)
    model = regression.linear_model.OLS(y, x).fit()
    return model.params[1]
def linres(y, x):
    y = np.array(y)
    x = sm.add_constant(np.array(x))
    model = regression.linear_model.OLS(y, x).fit()
    return model.resid
