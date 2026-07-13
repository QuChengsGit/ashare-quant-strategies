# 13、SVR因子选股策略

# 策略概述

“SVR因子选股策略”是一种基于支持向量回归（Support Vector Regression, SVR）的量化选股策略。该策略利用基本面因子和行业因子构建回归模型，评估股票的价值偏差，从而选择具有潜在超额收益的股票进行投资。策略通过动态调整持仓来优化投资组合，实现风险控制与收益的平衡。

# 策略优化与详细代码说明

## 1. 初始化函数

**函数名：initialize**

```python
def initialize(context):
    # 系统设置
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    set_option('avoid_future_data', True)
    # 策略调度
    run_daily(handle_training, 'before_open')
    run_daily(handle_trader, 'open')
```

**说明** ：

  * 初始化函数设置了策略的系统参数（如日志级别、真实价格交易、防未来数据等），并配置了每日策略的运行时机，包括模型训练和交易执行。

## 2. 策略主函数

**函数名：handle_training**

```python
def handle_training(context):
    # 参数设置
    n_position = 50  # 持股数
    n_choice = int(1.2 * n_position)  # 选股数，20%缓冲
    index = '399317.XSHE'  # 市场指数
    dt_last = context.previous_date
    # 获取当前市场股票池
    stocks = get_index_stocks(index, dt_last)
    # 获取基础财务数据
    q = query(
        valuation.code,
        valuation.market_cap,
        balance.total_assets - balance.total_liability,
        income.net_profit,
        balance.development_expenditure,
        valuation.pe_ratio,
        balance.total_assets / balance.total_liability,
        indicator.inc_revenue_year_on_year / 100
    ).filter(
        valuation.code.in_(stocks),
        balance.total_assets > balance.total_liability,
        income.net_profit > 0,
    )
    df = get_fundamentals(q, dt_last).fillna(0).set_index('code')
    df.columns = ['log_mc', 'log_NC', 'log_NI', 'log_RD', 'PE', 'lev', 'grow']
    # 对数变换
    def _sign_ln(X):
        return np.sign(X) * np.log(1.0 + np.abs(X))
    df['log_mc'] = _sign_ln(df['log_mc'])
    df['log_NC'] = _sign_ln(df['log_NC'])
    df['log_NI'] = _sign_ln(df['log_NI'])
    df['log_RD'] = _sign_ln(df['log_RD'])
    df['PE'] = _sign_ln(df['PE'])
    df['lev'] = _sign_ln(df['lev'])
    df['grow'] = _sign_ln(df['grow'])
    # 添加行业因子
    industry_list = get_industries('sw_l1', dt_last).index.tolist()
    for sector in industry_list:
        istocks = get_industry_stocks(sector, dt_last)
        s = pd.Series(0, index=df.index)
        s[set(istocks) & set(df.index)] = 1
        df[sector] = s
    # 训练SVR模型
    svr = SVR(kernel='rbf')
    Y = df['log_mc']
    X = df.drop('log_mc', axis=1)
    model = svr.fit(X, Y)
    # 选择具有价值偏差的股票
    residuals = Y - pd.Series(svr.predict(X), index=Y.index)
    choice = residuals[residuals < 0].sort_values().head(n_choice).index.tolist()
    # 保存结果
    g.choice = choice
    g.psize = 1.0 / n_position * context.portfolio.total_value
```

**说明** ：

  * handle_training函数在每日开盘前运行，进行SVR模型训练并选择股票。因子数据经过对数变换和行业因子补充后，SVR模型通过训练得到回归残差，基于负残差选出具有价值低估的股票。

**函数名：handle_trader**

```python
def handle_trader(context):
    # 获取交易参数
    choice = g.choice
    psize = g.psize
    cdata = get_current_data()
    # 卖出不在选股中的股票
    for s in context.portfolio.positions:
        if s not in choice and not cdata[s].paused:
            log.info('sell', s, cdata[s].name)
            order_target(s, 0, LimitOrderStyle(cdata[s].last_price))
    # 买入选中的股票
    for s in choice:
        if context.portfolio.available_cash < psize:
            break
        if s not in context.portfolio.positions and not cdata[s].paused:
            log.info('buy', s, cdata[s].name)
            order_value(s, psize, LimitOrderStyle(cdata[s].last_price))
```

**说明** ：

  * handle_trader函数在开盘时运行，执行调仓操作。首先卖出不再选股范围内的股票，然后按照模型预测结果买入新的股票。

## 3. 辅助功能

无额外辅助函数，该策略主要依赖于SVR模型进行选股与持仓调整。

### 策略适用场景

“SVR因子选股策略”适用于希望通过结合基本面与行业因子的机器学习模型来选股的投资者。该策略利用SVR模型评估股票的价值偏差，并动态调整持仓，实现收益与风险的平衡。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
