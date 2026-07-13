# 45、股票与期货混合动量与反转策略

# 1. 策略概述

本策略结合了股票选股和期货CTA策略，通过多因子选股和动量反转机制，选择优质股票进行投资。同时，通过期货市场的动量与波动率策略，在不同市场环境中适时调整持仓比例与头寸，力求在多样化市场中获取稳健收益。

# 2. 策略各部分功能代码详细技术文档说明

## 2.1 策略初始化 (initialize)

策略初始化时，设置了交易的基本参数，包括基准指数、滑点、交易成本等。并配置了股票子账户和期货子账户的资金比例，以及每个交易日的核心运行函数。

```python
def initialize(context):
    # 设置基准、真实价格、避免未来函数等系统选项
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    g.benchmark = '000905.XSHG'  # 中证500指数
    set_benchmark(g.benchmark)
    # 日志与显示格式设置
    log.set_level('order', 'error')
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.max_columns', 10)
    pd.set_option('display.width', 500)
    # 子账户资金分配
    g.stock_share = 0.7  # 股票账户占比
    g.future_share = 0.3  # 期货账户占比
    g.future_position = 0.35  # 期货账户中可用于持仓的比例
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash * g.stock_share, type='stock'),
                       SubPortfolioConfig(cash=context.portfolio.starting_cash * g.future_share, type='futures')])
    # 股票投资策略参数设置
    g.index = '399317.XSHE'  # 中证500指数成分股
    g.num = 5  # 每次选股数量
    g.stocks = []  # 当前股票池
    # 期货投资策略参数设置
    g.future_type = 'IC'  # 中证500期货
    g.futures_margin_rate = 0.15  # 期货保证金比例
    g.unitprice = 200  # 期货单位价格
    g.long_days = 5  # 开多均线天数
    g.short_days = 2  # 开空均线天数
    g.ATRdays = 20  # ATR止损参数
    g.boundrydays = 5  # 最高最低价区间长度
    g.stop = 5  # ATR止损倍数
    g.shortdays = 20  # 波动率计算短期天数
    g.longdays = 50  # 波动率计算长期天数
    g.para = 1  # 波动率调整参数
    g.day = 20  # 期货周期天数
    g.k = 1  # 期货初始交易手数
    g.day_count = g.day  # 初始化日计数
    # 期货交易相关设置
    set_order_cost(OrderCost(open_commission=0.000023, close_commission=0.000023, close_today_commission=0.0023), type='index_futures')
    set_option('futures_margin_rate', g.futures_margin_rate)
    set_slippage(StepRelatedSlippage(2))  # 期货交易滑点设置
    # 每日运行函数
    run_daily(handle_trader, time='13:45')  # 股票交易函数
    run_daily(before_market_open_future, time='9:00', reference_security='IF8888.CCFX')  # 期货开盘前准备
    run_daily(market_trade_future, time='11:15', reference_security='IF8888.CCFX')  # 期货交易函数
```

## 2.2 股票选股模块 (choice_stocks)

该模块通过基本面因子筛选股票，结合市值、股息率等多因子筛选出目标股票池，并按股息率进行排序，选出表现最好的若干只股票。

```python
def choice_stocks(context, index, num):
    # 获取指数成分股列表
    stocks = get_index_stocks(index)
    # 过滤并筛选股票
    sdf = get_fundamentals(query(
            valuation.code,
            valuation.market_cap,  # 市值（亿元）
        ).filter(
            valuation.code.in_(stocks),
            valuation.pb_ratio < 3,
            valuation.pb_ratio > 0,
            indicator.roe > 0.1,
            balance.cash_equivalents > 0.4 * balance.shortterm_loan,
            indicator.roa > 0.05 * indicator.roe,
            balance.total_assets / balance.total_liability > 1,
            indicator.roa > 0,
            valuation.pe_ratio > 0,
            valuation.ps_ratio > 0,
            valuation.pcf_ratio > 0,
            indicator.inc_revenue_year_on_year > 10,
            indicator.inc_net_profit_to_shareholders_year_on_year > 10,
        )).dropna().set_index('code')
    # 获取最近三年内的分红数据
    dt_3y = context.current_dt.date() - dt.timedelta(days=3*365)
    ddf = finance.run_query(query(
            finance.STK_XR_XD.code,
            finance.STK_XR_XD.company_name,
            finance.STK_XR_XD.board_plan_pub_date,
            finance.STK_XR_XD.bonus_amount_rmb,  # 分红金额（万元）
        ).filter(
            finance.STK_XR_XD.code.in_(stocks),
            finance.STK_XR_XD.board_plan_pub_date > dt_3y,
            finance.STK_XR_XD.bonus_amount_rmb > 0
        )).dropna()
    # 计算股息率
    divy = pd.Series(data=np.zeros(len(stocks)), index=stocks)
    for k in ddf.index:
        s = ddf.code[k]
        divy[s] += ddf.bonus_amount_rmb[k]
    sdf = sdf.reindex(stocks)
    sdf['div_3y'] = divy
    sdf['div_ratio'] = 1e-2 * sdf.div_3y / sdf.market_cap
    sdf = sdf.sort_values(by='div_ratio', ascending=False)
    log.info('\n', sdf[:5])
    return list(sdf.head(num).index)
```

## 2.3 资金管理与调仓模块 (rebalance)

通过计算当前股票子账户与期货子账户的资金比例，调整子账户之间的资金分配，确保两个账户的资金配置符合预期。

```python
def rebalance(context):
    total_value = context.portfolio.total_value
    expected_stock_value = total_value * g.stock_share
    # 资金划转，确保各子账户资金比例
    transfer_cash(1, 0, min(context.subportfolios[1].transferable_cash, max(0, expected_stock_value-context.subportfolios[0].total_value)))
    transfer_cash(0, 1, min(context.subportfolios[0].transferable_cash, max(0, context.subportfolios[0].total_value-expected_stock_value)))
    stock_value = min(context.subportfolios[0].total_value, expected_stock_value)
```

## 2.4 期货交易模块 (market_trade_future)

通过动量和波动率因子判断市场趋势，结合ATR止损机制，在波动率较低时加仓，在市场趋势明确时进行开仓操作。

```python
def market_trade_future(context):
    g.sign = update_niu_signal(context, g.benchmark)
    g.loss_stop = loss_stop(context, g.benchmark)
    g.volatility = volatility(context, g.benchmark)
    # 根据波动率调整持仓手数
    if g.volatility == -1:
        future_position = int(1.5 * g.k)
    elif g.volatility == 1:
        future_position = int(1 * g.k)
    # 开仓信号
    if (len(context.subportfolios[1].long_positions) == 0) & (len(context.subportfolios[1].short_positions) == 0):
        if g.sign > 0:
            order(g.code_1, future_position, side='long', pindex=1)
        elif g.sign < 0:
            order(g.code_1, future_position, side='short', pindex=1)
    # 平仓信号
    elif (len(context.subportfolios[1].long_positions) + len(context.subportfolios[1].short_positions)) > 0:
        if g.de_day == 0:
            # ATR止损
            if (len(context.subportfolios[1].long_positions) > 0) & (g.loss_stop == 1):
                order_target(g.code_1, 0, side='long', pindex=1)
            elif (len(context.subportfolios[1].short_positions) > 0) & (g.loss_stop == 1):
                order_target(g.code_1, 0, side
='short', pindex=1)
            # 平开仓信号
            elif (len(context.subportfolios[1].long_positions) > 0) & (g.sign == 0):
                order_target(g.code_1, 0, side='long', pindex=1)
                order(g.code_1, future_position, side='short', pindex=1)
            elif (len(context.subportfolios[1].short_positions) > 0) & (g.sign > 0):
                order_target(g.code_1, 0, side='short', pindex=1)
                order(g.code_1, future_position, side='long', pindex=1)
        else:
            # 交割日平仓
            if len(context.subportfolios[1].long_positions) > 0:
                order_target(g.code_1, 0, side='long', pindex=1)
            else:
                order_target(g.code_1, 0, side='short', pindex=1)
```

## 2.5 辅助模块

包括更新交易信号、波动率计算、ATR止损等功能，用于支持主策略的运行。

```python
def volatility(context, ind):
    current_ATR_a = ATR(ind, context.current_dt, g.shortdays)
    current_ATR_b = ATR(ind, context.current_dt, g.longdays)
    k = current_ATR_a[-1][ind] - g.para * current_ATR_b[-1][ind]
    if k < 0:
        return -1  # 波动率低，可重仓
    elif k > 0:
        return 1  # 波动率高，可轻仓
```

# 3. 策略优化建议

  1. **参数优化** ：通过回测优化各个参数（如g.k、g.stop等），提升策略的表现。

  2. **动态调仓** ：在不同市场环境下，动态调整股票与期货的配置比例，以更好地平衡风险和收益。

  3. **多因子选股** ：引入更多的财务因子进行选股，以提升股票池的质量。

  4. **风险控制** ：引入最大回撤、止盈等风控措施，减少策略在极端市场环境下的损失。

该策略结合股票与期货市场，通过多因子选股和动量策略，在不同市场环境下进行灵活调整，力求在多样化市场中获取稳健收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
