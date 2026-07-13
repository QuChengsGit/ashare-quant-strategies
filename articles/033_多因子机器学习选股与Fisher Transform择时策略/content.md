# 33、多因子机器学习选股与Fisher Transform择时策略

# 1. 策略概述

本策略结合多因子分析与机器学习模型，通过支持向量回归（SVR）对股票进行打分和排序，并在择时上结合Fisher Transform进行交易信号生成，筛选出表现最优的股票进行投资。该策略旨在通过量化因子和机器学习算法的结合，实现稳健的投资收益。

# 2. 模块及代码功能说明

## 2.1 初始化模块 (initialize)

该模块用于设置策略的基本参数和回测环境，包括因子选取、调仓周期、持仓数量等。

```python
def initialize(context):
    set_params()
    set_backtest()
    g.factors = ['alpha_006', 'alpha_015', 'alpha_026']  # 选取的alpha因子
```

## 2.2 参数设置模块 (set_params)

用于初始化策略的全局参数，包括调仓周期、持仓股票数量等。

```python
def set_params():
    g.days = 0           # 日期计数器
    g.refresh_rate = 10   # 调仓间隔周期
    g.stocknum = 3        # 持仓股票数量
```

## 2.3 回测环境设置模块 (set_backtest)

设置回测环境参数，如交易成本、基准、滑点等。

```python
def set_backtest():
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    log.set_level('order', 'error')
```

## 2.4 股票过滤模块 (filter_stock_ST, filter_stock_limit, remove_new_stocks)

这些模块用于在选股和交易时过滤掉不符合条件的股票，如停牌、ST股、涨跌停股以及上市时间不足180天的次新股。

```python
def filter_stock_ST(stock_list):
    curr_data = get_current_data()
    return [stock for stock in stock_list if not (curr_data[stock].paused or curr_data[stock].is_st or 'ST' in curr_data[stock].name or '*' in curr_data[stock].name or '退' in curr_data[stock].name)]
def filter_stock_limit(stock_list):
    curr_data = get_current_data()
    return [stock for stock in stock_list if not (curr_data[stock].high_limit <= curr_data[stock].day_open or curr_data[stock].day_open <= curr_data[stock].low_limit)]
def remove_new_stocks(security_list, context):
    return [stock for stock in security_list if (context.current_dt.date() - get_security_info(stock).start_date).days >= 180]
```

## 2.5 数据获取与因子计算模块 (getStockPrice, df_neutralization, linreg, linres)

这些模块用于获取股票历史数据，计算回归模型的因子值，并对因子进行中性化处理。

```python
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
```

## 2.6 择时模块 (fisher_transform_strategy)

通过Fisher Transform技术指标，判断当前市场是否适合买入，并筛选出可以买入的股票。

```python
def fisher_transform_strategy(context, security_list):
    buyable_stocks = []
    end_date = context.previous_date
    period = 10
    def fisher_transform(data, period=period):
        high = data['high']
        low = data['low']
        close = data['close']
        mid_price = (high + low) / 2.0
        typical_price = (high + low + close) / 3.0
        smoothed_price = (mid_price + typical_price) / 2.0
        price_diff = typical_price - mid_price
        abs_diff = np.abs(price_diff)
        fisher = np.log((1 + abs_diff) / (1 - abs_diff))
        return fisher
    for security in security_list:
        df = get_price(security, end_date=end_date, count=period, panel=False, fill_paused=False)
        df['fisher'] = fisher_transform(df)
        if df['fisher'].iloc[-1] > 0:
            buyable_stocks.append(security)
    return buyable_stocks
```

## 2.7 交易模块 (handle_data)

这是策略的核心模块，每个调仓周期触发，执行因子计算、SVR模型训练、择时判断，并最终生成交易指令。

```python
def handle_data(context, data):
    if g.days % g.refresh_rate == 0:
        sample = get_index_stocks('000985.XSHG', date=None)
        sample = filter_stock_ST(sample)
        sample = remove_new_stocks(sample, context)
        sample = filter_stock_limit(sample)
        q = query(valuation.code,
                  valuation.market_cap,
                  indicator.roe / valuation.pb_ratio,
                  valuation.pe_ratio / indicator.inc_net_profit_year_on_year
                 ).filter(
                     valuation.pe_ratio < 100,
                     valuation.market_cap < 1000,
                     valuation.code.in_(sample)
                 ).order_by(
                     (valuation.pe_ratio / indicator.inc_net_profit_year_on_year).asc()
                 ).limit(500)
        df = get_fundamentals(q, date=None)
        select_list = list(df['code'])
        for factor in g.factors:
            df[factor] = np.array(eval(factor)(select_list, end_date=None))
        momentum = []
        for i in select_list:
            interval, Yesterday = getStockPrice(i, g.refresh_rate)
            stock_momentum = Yesterday / interval - 1
            momentum.append((i, stock_momentum))
        np_momentuma = np.array(momentum)
        momentum_value = np_momentuma[:, 1].astype(float).tolist()
        df['momentum_value'] = momentum_value
        df.columns = ['code', 'market_cap', 'PB_ROE', 'PE_G', g.factors[0], g.factors[1], g.factors[2], 'momentum_value']
        df = df_neutralization(df, 'market_cap')
        df.index = df.code.values
        del df['code']
        df = df.fillna(0)
        X = df[g.factors]
        Y = df[['market_cap']]
        X = X.fillna(0)
        Y = Y.fillna(0)
        svr = SVR(kernel='poly', gamma=0.01)
        model = svr.fit(X, Y)
        predict = svr.predict(X)
        record(R2=r2_score(Y, predict))
        record(MAE=mean_absolute_error(Y, predict))
        record(MSE=mean_squared_error(Y, predict))
        record(EVS=explained_variance_score(Y, predict))
        factor = Y - pd.DataFrame(predict, index=Y.index, columns=['market_cap'])
        factor = factor.sort_index(by='market_cap', ascending=True)
        order_list = fisher_transform_strategy(context, list(factor.index))[:g.stocknum]
        order_stock_sell(context, order_list)
        order_stock_buy(context, order_list)
        g.days += 1
    else:
        g.days += 1
```

## 2.8 执行卖出与买入模块 (order_stock_sell, order_stock_buy)

这些模块执行最终的交易指令，卖出不符合条件的股票，买入筛选后的优质股票。

```python
def order_stock_sell(context, order_list):
    for stock in context.portfolio.positions:
        if stock not in order_list:
            order_target_value(stock, 0)
def order_stock_buy(context, order_list):
    if len(context.portfolio.positions) < g.stocknum:
        num = g.stocknum - len(context.portfolio.positions)
        g.each_stock_cash = context.portfolio.cash / num
    for stock in order_list:
        if stock not in context.portfolio.positions:
            order_target_value(stock, g.each_stock_cash)
```

# 3. 策略优化建议

  1. **因子优化** ：根据回测结果调整因子权重或选择更合适的因子，进一步提升策略表现。

  2. **模型改进** ：考虑引入其他机器学习模型（如随机森林、神经网络）进行因子打分，以提高模型的鲁棒性。

  3. **风险控制** ：结合止损策略或动态仓位调整，进一步降低投资风险。

该策略通过多因子分析与机器学习模型的结合，辅以Fisher Transform择时机制，实现了对市场的深度把握和优质股票的筛选，有望在市场波动中获得稳健收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
