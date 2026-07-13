# 102、动量共振ETF猎手

## 策略概述

本策略是一个基于技术分析和市场择时的量化交易策略，主要用于ETF（交易型开放式指数基金）的买卖。策略的核心思想是通过分析大盘指数和行业指数的动量，结合BBI（多空指标）和EMA（指数移动平均线）等技术指标，判断市场趋势并进行相应的买卖操作。策略的目标是在牛市中买入表现强势的ETF，在熊市中清仓或减少持仓，以实现资产的保值增值。

## 策略详细介绍

### 1. 初始化设置

在策略的初始化阶段，进行了以下设置：

```python
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    set_slippage(FixedSlippage(0.004))
    set_option("avoid_future_data", True)
    set_option('use_real_price', True)
    log.info('初始函数开始运行且全局只运行一次')
    set_order_cost(OrderCost(close_tax=0.00, open_commission=0.00015, close_commission=0.00015, min_commission=5), type='fund')
    run_daily(make_sure_etf_ipo, time='9:15')
    run_weekly(market_buy, weekday=3, time='11:15')
    g.dapan_threshold = 0
    g.signal = 'BUY'
    g.niu_signal = 1
    g.position = 1
    g.lag1 = 20
    g.decrease_days = 0
    g.increase_days = 0
    g.unit = '30m'
    g.bond = '511880.XSHG'
    g.zs_list = [
        '000001.XSHG', '399001.XSHE', '000300.XSHG', '000905.XSHG', '000852.XSHG', '399006.XSHE', '000688.XSHG'
    ]
    g.ETF_list = {
        '000986.XSHG': '515220.XSHG', '000827.XSHG': '516070.XSHG', '399967.XSHE': '512660.XSHG', '000995.XSHG': '159611.XSHE',
        '000987.XSHG': '159944.XSHE', '000813.XSHG': '516120.XSHG', '000989.XSHG': '159928.XSHE', '399997.XSHE': '512690.XSHG',
        '000991.XSHG': '512170.XSHG', '399971.XSHE': '512980.XSHG', '399986.XSHE': '512800.XSHG', '399975.XSHE': '159841.XSHE',
        '000993.XSHG': '512480.XSHG', '000922.XSHG': '515080.XSHG', '399440.XSHE': '515210.XSHG', '399814.XSHE': '159825.XSHE',
        '399995.XSHE': '516970.XSHG'
    }
    g.not_ipo_list = g.ETF_list.copy()
    g.available_indexs = []
```

  * **基准设定** ：将沪深300指数（000300.XSHG）设定为基准。

  * **滑点设置** ：使用固定滑点（0.004），避免因市场波动导致的成交价格偏差。

  * **复权模式** ：开启动态复权模式，使用真实价格进行交易。

  * **手续费设置** ：设定ETF交易的手续费为万分之一点五，无印花税。

  * **运行时间** ：设定每周三中午11:15进行交易，并在每天开盘时检查ETF是否上市。

### 2. 数据准备

```python
g.zs_list = [
    '000001.XSHG', '399001.XSHE', '000300.XSHG', '000905.XSHG', '000852.XSHG', '399006.XSHE', '000688.XSHG'
]
g.ETF_list = {
    '000986.XSHG': '515220.XSHG', '000827.XSHG': '516070.XSHG', '399967.XSHE': '512660.XSHG', '000995.XSHG': '159611.XSHE',
    '000987.XSHG': '159944.XSHE', '000813.XSHG': '516120.XSHG', '000989.XSHG': '159928.XSHE', '399997.XSHE': '512690.XSHG',
    '000991.XSHG': '512170.XSHG', '399971.XSHE': '512980.XSHG', '399986.XSHE': '512800.XSHG', '399975.XSHE': '159841.XSHE',
    '000993.XSHG': '512480.XSHG', '000922.XSHG': '515080.XSHG', '399440.XSHE': '515210.XSHG', '399814.XSHE': '159825.XSHE',
    '399995.XSHE': '516970.XSHG'
}
g.not_ipo_list = g.ETF_list.copy()
g.available_indexs = []
```

  * **大盘指数列表** ：包含上证综指、深证成指、沪深300等主要大盘指数。

  * **行业指数与ETF对应关系** ：建立行业指数与对应ETF的映射关系，确保在交易时能够快速找到对应的ETF。

  * **可交易指数列表** ：初始化时复制行业指数与ETF的映射关系，并在后续交易中动态更新，确保只交易已上市的ETF。

### 3. 交易逻辑

3.1 市场买入逻辑

```python
def market_buy(context):
    df_index = pd.DataFrame(columns=['指数代码', '周期动量'])
    df_incre = pd.DataFrame(columns=['大盘代码', '周期涨幅', '当前价格'])
    unit = g.unit
    BBI2 = BBI(g.available_indexs, check_date=context.current_dt, timeperiod1=21, timeperiod2=34, timeperiod3=55, timeperiod4=89, unit=unit, include_now=True)
    for index in g.available_indexs:
        df_close = get_bars(index, 1, unit, ['close'], end_dt=context.current_dt, include_now=True)['close']
        val = BBI2[index] / df_close[0]
        df_index = df_index.append({'指数代码': index, '周期动量': val}, ignore_index=True)
    df_index.sort_values(by='周期动量', ascending=False, inplace=True)
    log.info(df_index)
    target = df_index['指数代码'].iloc[-1]
    target_bbi = df_index['周期动量'].iloc[-1]
    for index in g.zs_list:
        df_close = get_bars(index, 3, '1d', ['close'], end_dt=context.current_dt, include_now=True)['close']
        if len(df_close) > 2:
            increase_previous = (df_close[1] - df_close[0]) / df_close[0]
            increase = (df_close[2] - df_close[1]) / df_close[1]
            increase_delta = (df_close[2] - df_close[1]) / df_close[1] - 0.25 * (df_close[1] - df_close[0]) / df_close[0]
            df_incre = df_incre.append({'大盘代码': index, '前周期涨幅': increase, '本周期涨幅': increase, '本周期涨幅变动': increase_delta, '当前价格': df_close[0]}, ignore_index=True)
    df_incre.sort_values(by='本周期涨幅', ascending=False, inplace=True)
    print(df_incre)
    today_increase_previous = df_incre['前周期涨幅'].iloc[0]
    today_increase = df_incre['本周期涨幅'].iloc[0]
    today_increase_delta = df_incre['本周期涨幅变动'].iloc[0]
    today_index_code = df_incre['大盘代码'].iloc[0]
    today_index_close = df_incre['当前价格'].iloc[0]
    holdings = set(context.portfolio.positions.keys())
    update_niu_signal(context, today_index_code)
    if (context.current_dt.hour == 11 and g.niu_signal == 0 and g.signal == 'BUY') or (context.current_dt.hour == 14 and g.niu_signal == 1):
        log.info('牛熊不匹配，这个时间点不能开仓，并清仓')
        for etf in holdings:
            if etf == g.bond:
                log.info('相同etf，不需要调仓！@')
                return
            else:
                order_target(etf, 0)
                order_value(g.bond, context.portfolio.available_cash)
        return
    if today_increase > g.dapan_threshold and today_increase > 0.05 * today_increase_previous and target_bbi < 1:
        g.signal = 'BUY'
        g.increase_days += 1
    else:
        g.signal = 'CLEAR'
        g.decrease_days += 1
    log.info("-------------increase_days----------- %s" % (g.increase_days))
    log.info("-------------decrease_days----------- %s" % (g.decrease_days))
    target_etf = g.ETF_list[target]
    if g.signal == 'CLEAR':
        for etf in holdings:
            log.info("----~~~---指数集体下跌，卖出---~~~~~~-------- %s" % (etf))
            if etf == g.bond:
                log.info('相同etf，不需要调仓！@')
                return
            else:
                order_target(etf, 0)
                order_value(g.bond, context.portfolio.available_cash)
        return
    else:
        for etf in holdings:
            if etf == target_etf:
                log.info('相同etf，不需要调仓！@')
                return
            else:
                order_target(etf, 0)
                log.info("------------------调仓卖出----------- %s" % (etf))
        log.info("------------------买入----------- %s" % (target))
        order_value(target_etf, context.portfolio.available_cash * g.position)
```

  * **动量分析** ：通过BBI指标计算各指数的动量，选择动量最小的指数对应的ETF进行买入。

  * **大盘涨幅判断** ：计算大盘指数的涨幅，判断市场整体趋势。如果大盘涨幅超过设定的阈值且BBI指标小于1，则认为市场处于多头状态，进行买入操作。

  * **牛熊信号更新** ：根据300ETF的5日均线判断市场趋势，决定是否进行交易。如果价格低于5日均线且均线呈空头排列，则暂停交易。

3.2 清仓逻辑

```python
if (context.current_dt.hour == 11 and g.niu_signal == 0 and g.signal == 'BUY') or (context.current_dt.hour == 14 and g.niu_signal == 1):
    log.info('牛熊不匹配，这个时间点不能开仓，并清仓')
    for etf in holdings:
        if etf == g.bond:
            log.info('相同etf，不需要调仓！@')
            return
        else:
            order_target(etf, 0)
            order_value(g.bond, context.portfolio.available_cash)
    return
if today_increase > g.dapan_threshold and today_increase > 0.05 * today_increase_previous and target_bbi < 1:
    g.signal = 'BUY'
    g.increase_days += 1
else:
    g.signal = 'CLEAR'
    g.decrease_days += 1
log.info("-------------increase_days----------- %s" % (g.increase_days))
log.info("-------------decrease_days----------- %s" % (g.decrease_days))
target_etf = g.ETF_list[target]
if g.signal == 'CLEAR':
    for etf in holdings:
        log.info("----~~~---指数集体下跌，卖出---~~~~~~-------- %s" % (etf))
        if etf == g.bond:
            log.info('相同etf，不需要调仓！@')
            return
        else:
            order_target(etf, 0)
            order_value(g.bond, context.portfolio.available_cash)
    return
else:
    for etf in holdings:
        if etf == target_etf:
            log.info('相同etf，不需要调仓！@')
            return
        else:
            order_target(etf, 0)
            log.info("------------------调仓卖出----------- %s" % (etf))
    log.info("------------------买入----------- %s" % (target))
    order_value(target_etf, context.portfolio.available_cash * g.position)
```

  * **市场下跌判断** ：如果大盘指数下跌或涨幅未达到预期，则进行清仓操作，将资金转入货币基金（如银华日利）。

  * **时间控制** ：根据牛熊信号和当前时间，决定是否进行清仓操作。例如，在熊市中上午不进行交易，下午进行清仓。

### 4. 辅助函数

4.1 获取交易日

```python
def get_before_after_trade_days(date, count, is_before=True):
    all_date = pd.Series(get_all_trade_days())
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    if isinstance(date, datetime.datetime):
        date = date.date()
    if is_before:
        return all_date[all_date <= date].tail(count).values[0]
    else:
        return all_date[all_date >= date].head(count).values[-1]
```

  * **获取交易日** ：通过get_before_after_trade_days函数获取指定日期前后的交易日，用于判断ETF是否已上市。

4.2 ETF上市检查

```python
def make_sure_etf_ipo(context):
    if len(g.not_ipo_list) == 0:
        return
    idxs = []
    yesterday = context.previous_date
    list_date = get_before_after_trade_days(yesterday, g.lag1)
    all_funds = get_all_securities(types='fund', date=yesterday)
    all_idxes = get_all_securities(types='index', date=yesterday)
    for idx in g.not_ipo_list:
        if idx in all_idxes.index:
            if all_idxes.loc[idx].start_date <= list_date:
                symbol = g.not_ipo_list[idx]
                if symbol in all_funds.index:
                    if all_funds.loc[symbol].start_date <= list_date:
                        g.available_indexs.append(idx)
                        idxs.append(idx)
    for idx in idxs:
        del g.not_ipo_list[idx]
    return
```

  * **ETF上市检查** ：在每天开盘时运行make_sure_etf_ipo函数，确保交易的ETF已经上市超过一定天数（如20天）。

## 总结

本策略通过结合大盘指数和行业指数的动量分析，以及BBI和EMA等技术指标，实现了对市场趋势的判断和相应的买卖操作。策略的核心在于通过技术分析捕捉市场的短期趋势，并在趋势确认后进行交易。同时，策略通过设定合理的滑点和手续费，以及动态复权模式，确保交易的准确性和成本控制。总体而言，该策略适合在波动较大的市场中使用，能够有效捕捉短期交易机会，实现资产的增值。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
