# 73、精准溢价套利ETF策略

# 策略概述

该策略以沪深300指数为基准，通过分析ETF基金的溢价率进行交易决策。策略的核心思想是利用ETF的市场价格与净值之间的偏差进行套利。当ETF的市场价格相对于其净值出现较大溢价或折价时，策略会分别进行卖出或买入操作，以期获得无风险收益。该策略特别适用于日内交易，通过实时监控市场价格与净值的变化，在合适的时机执行交易。

### 核心功能代码

```python
from jqdata import *
import datetime
import talib
from jqlib.technical_analysis import *
import sys
import requests
## 初始化函数，设定基准等
def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.00025,
                             close_commission=0.00025, close_today_commission=0, min_commission=5),
                   type='fund')
    log.set_level('order', 'error')
    g.least_premium = 2.5
    g.least_money = 1.0e7
    g.trade_fee_ratio = 0.00025
    g.ETFNum_hold = 2
    g.etf_df = []
    do_schedule(context)
def after_code_changed(context):
    unschedule_all()
    do_schedule(context)
def do_schedule(context):
    run_daily(pre_process, '09:15', reference_security='000300.XSHG')
    run_daily(exe_sell, '09:30', reference_security='000300.XSHG')
    run_daily(exe_buy, '09:30', reference_security='000300.XSHG')
def pre_process(context):
    etf_list = get_all_securities(['etf'], context.previous_date).index.tolist()
    df = history(count=1, unit='1d', field="money", security_list=etf_list).T
    df.columns = ['money']
    df = df[df.money > g.least_money]
    today = datetime.datetime.now().date().strftime("%Y-%m-%d")
    current_dt = context.current_dt.strftime("%Y-%m-%d")
    if current_dt < today:
        df = get_extras('unit_net_value', df.index.tolist(), end_date=context.previous_date, df=True, count=1).T
        df.columns = ['unit_net_value']
    else:
        df['unit_net_value'] = [get_etf_value(etf) for etf in df.index.tolist()]
        df = df[df.unit_net_value != -1]
    g.etf_df = df
def exe_sell(context):
    df = g.etf_df
    current = get_current_data()
    df['day_open'] = [current[c].day_open for c in df.index.tolist()]
    df['premium'] = (df.day_open / df.unit_net_value - 1) * 100
    df['factor'] = [attribute_history(c, 1, '1d', fields=['factor'])['factor'][-1] for c in df.index.tolist()]
    df = df[df['factor'] == 1]
    df = df[abs(df['premium']) < 20]
    df = df.sort_values(['premium'], ascending=True)
    df = df[df.premium < -1.0 * g.least_premium]
    order_etf = df[:g.ETFNum_hold].index.tolist()
    etf_to_sell = list(set(context.portfolio.positions.keys()) - set(order_etf))
    for etf in etf_to_sell:
        if context.portfolio.positions[etf].closeable_amount:
            limit_price = current[etf].day_open * 0.98
            order_sell = order_target(etf, 0, LimitOrderStyle(limit_price))
            if order_sell:
                log.info("成功卖出基金 %s【%s】" %  (get_security_info(etf).display_name, etf))
            else:
                log.info("未成功卖出基金 %s【%s】" %  (get_security_info(etf).display_name, etf))
def exe_buy(context):
    least_money_to_buy = 5.00 / g.trade_fee_ratio
    if context.portfolio.available_cash < least_money_to_buy:
        return
    current = get_current_data()
    df = g.etf_df
    df['day_open'] = [current[c].day_open for c in df.index.tolist()]
    df['premium'] = (df.day_open / df.unit_net_value - 1) * 100
    df['factor'] = [attribute_history(c, 1, '1d', fields=['factor'])['factor'][-1] for c in df.index.tolist()]
    df = df[df['factor'] == 1]
    df = df[abs(df['premium']) < 20]
    df = df.sort_values(['premium'], ascending=True)
    df = df[df.premium < -1.0 * g.least_premium]
    order_etf = df[:g.ETFNum_hold].index.tolist()
    to_buy_set = set(order_etf) | set(context.portfolio.positions.keys())
    to_buy_list = list(to_buy_set)
    cash_per_etf = context.portfolio.available_cash / len(to_buy_list)
    if cash_per_etf > least_money_to_buy:
        for etf in to_buy_list:
            limit_price = current[etf].day_open * 1.02
            num_to_buy = int(cash_per_etf / (limit_price * 1.005 * 1.00025) / 100) * 100
            order_buy = order_target(etf, num_to_buy, LimitOrderStyle(limit_price))
            if order_buy:
                log.info("成功买入基金 %s【%s】：%s 股" %  (get_security_info(etf).display_name, etf, order_buy.filled))
            else:
                log.info("未成功买入基金 %s【%s】" %  (get_security_info(etf).display_name, etf))
def after_trading_end(context):
    log.info('交易日结束，感谢参与！')
def get_etf_value(stockcode):
    stockcode = stockcode[:6]
    url = "http://etf.eastmoney.com/" + stockcode + ".html"
    response = requests.get(url)
    etfDataInfo = response.text
    tmp_str = "fix_dwjz  bold ui-color-green"
    init_position = etfDataInfo.find(tmp_str)
    if init_position == -1:
        return -1
    else:
        init_position += len(tmp_str)
        etf_value = float(etfDataInfo[init_position + 2:init_position + 8])
        return etf_value
```

### 技术文档说明

1\. 初始化函数 (initialize)

  * **功能** : 设置交易基准、启用真实价格、配置手续费及其他全局参数，并安排每日定时任务。

  * **主要参数** :

    * set_benchmark('000300.XSHG'): 将沪深300指数设为基准。

    * g.least_premium: 最小溢价百分比，决定买卖操作的阈值。

    * g.least_money: 最小成交金额过滤条件，单位为元。

    * g.ETFNum_hold: 最大持有的ETF数量。

2\. 定时任务调度 (do_schedule)

  * **功能** : 安排每日的定时任务，包括预处理数据、执行买卖操作。

  * **任务** :

    * pre_process: 每日预处理ETF数据，过滤符合条件的ETF。

    * exe_sell: 执行卖出操作，根据溢价率选择卖出ETF。

    * exe_buy: 执行买入操作，选择符合条件的ETF进行买入。

3\. 数据预处理 (pre_process)

  * **功能** : 获取并过滤ETF数据，计算每只ETF的净值与溢价率，并存储在全局变量中以备后续使用。

  * **逻辑** :

    * 通过聚宽API或自编爬虫函数获取ETF净值。

    * 过滤掉成交金额小于指定阈值和净值异常的ETF。

4\. 卖出函数 (exe_sell)

  * **功能** : 根据溢价率的大小选择合适的ETF进行卖出操作。

  * **逻辑** :

    * 计算每只持有ETF的开盘价和溢价率。

    * 如果溢价率超过指定阈值，执行卖出操作。

5\. 买入函数 (exe_buy)

  * **功能** : 选择符合条件的ETF进行买入操作。

  * **逻辑** :

    * 计算每只ETF的开盘价和溢价率。

    * 根据现金余额和ETF数量分配资金，执行买入操作。

6\. 交易结束处理 (after_trading_end)

  * **功能** : 记录和总结每日交易结束时的情况。

7\. ETF净值获取函数 (get_etf_value)

  * **功能** : 通过东方财富

网获取指定ETF的最新净值。

  * **技术** : 使用requests库抓取网页内容并解析出净值数据。

### 优化改进要点

  * 简化代码逻辑，提高代码可读性和执行效率。

  * 增加对ETF净值数据的实时性获取处理，确保交易决策的准确性。

  * 强化溢价率计算的稳定性，避免因极端市场情况导致的错误决策。

  * 自动调整参数配置，如最小溢价率和最小成交金额，以适应不同的市场环境。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
