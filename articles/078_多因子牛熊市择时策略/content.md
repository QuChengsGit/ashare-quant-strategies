# 78、多因子牛熊市择时策略

# 策略概述

**多因子牛熊市择时策略** 结合了多因子选股和牛熊市判断，通过动态调整股债仓位比例，实现稳健的收益增长。该策略通过技术指标和多因子模型筛选出优质股票，同时根据市场趋势判断（牛市或熊市）进行股债动态调整，确保在市场不同阶段都能灵活配置仓位，以应对市场波动。

### 核心功能代码优化

```python
from jqdata import *
from jqfactor import *
import pandas as pd
import numpy as np
import time
from six import BytesIO
# 初始化函数，设定基准等等
def initialize(context):
    # 最大持仓数量
    g.max_stock_count = 5
    # 牛熊市场参数设定
    g.MA = ['399008.XSHE', 10]  # 中小300指数和均线周期
    g.threshold = 0.003  # 牛熊切换阈值
    g.isbull = False  # 当前是否为牛市
    g.bearpercent = 0.5  # 熊市股票持仓比例（原值为30%）
    # 交易规则参数
    g.hold_interval = 10  # 最短持仓时间（天）
    g.selldate_interval = 5  # 卖出后再买入间隔时间（天）
    g.top_withdraw_ratio = 0.03  # 最高点回撤比例
    # 债券基金
    g.bond = '511010.XSHG'
    # 交易统计与记录
    g.statistics_df = pd.DataFrame(columns=['code', 'name', 'date_buy', 'price_buy', 'date_sell', 'price_sell', 'ratio', 'result'])
    g.sell_history_df = pd.DataFrame(columns=['code', 'name', 'last_date_sell'])
    # 股票名称缓存
    g.stocks_allnames_df = get_all_securities()
    # 设置基准为沪深300
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    set_option("avoid_future_data", True)
    log.info('策略初始化完成')
    log.set_level('order', 'error')
    # 设置股票交易费用
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 定时任务
    run_daily(before_market_open, time='before_open')
    run_daily(market_open, time='14:55')
    run_daily(after_market_close, time='after_close')
## 开盘前运行函数
def before_market_open(context):
    pass
## 开盘时运行函数
def market_open(context):
    date = context.current_dt.strftime("%Y-%m-%d")
    # 判断牛熊趋势
    get_bull_bear_signal_minute()
    # 建仓程序
    buy_df = get_df_fromfile(context)
    buylist = buy_df['code'].tolist()
    if not buylist:
        log.info('当日无建仓信号')
    else:
        log.info('今日建仓列表:' + str(buy_df))
        adjust_position(context, buylist)
## 收盘后运行函数
def after_market_close(context):
    log.info('############################一天结束###############################')
def on_strategy_end(context):
    log.info('策略执行结束，总资产 = ' + str(context.portfolio.total_value))
# 获取当天的买入信号CSV文件，返回待买入股票列表的df
def get_df_fromfile(context):
    date = context.current_dt.strftime("%Y-%m-%d")
    file_name = f'8.Mutifactors/Signal_for_trade_{date}.csv'
    log.info('读取买入信号文件：' + str(file_name))
    return pd.read_csv(BytesIO(read_file(file_name)))
# 调仓函数，输入股票列表，自动完成调仓操作
def adjust_position(context, buylist):
    date = context.current_dt.strftime("%Y-%m-%d")
    total_value = round(context.portfolio.total_value, 2)
    # 牛熊市判断及仓位调整
    if g.isbull:
        log.info('当前牛市，股票满仓')
        mkt_ratio = 1
    else:
        log.info('当前熊市，股债搭配')
        mkt_ratio = g.bearpercent
    positions_value_stock = round(total_value * mkt_ratio, 2)
    positions_value_bond = round(total_value - positions_value_stock, 2)
    # 止盈与清仓
    for stock in context.portfolio.positions.keys():
        avg_cost = context.portfolio.positions[stock].avg_cost
        current_price = context.portfolio.positions[stock].price
        buy_in_date = context.portfolio.positions[stock].init_time.strftime('%Y-%m-%d')
        df_price = get_price(stock, start_date=buy_in_date, end_date=context.previous_date, frequency='daily', fields=['close'])
        max_price = df_price['close'].max()
        final_profit_ratio = (current_price / avg_cost) - 1
        if (stock != g.bond) and ((1 - (current_price / max_price)) > g.top_withdraw_ratio):
            order_target_value(stock, 0)
            log.info(f'个股止盈清仓: {stock} 盈利比例: {round(final_profit_ratio * 100, 2)}%')
            continue
        if (stock != g.bond) and check_hold_interval(context, stock, g.hold_interval):
            order_target_value(stock, 0)
            log.info(f'个股到期清仓: {stock} 盈利比例: {round(final_profit_ratio * 100, 2)}%')
    # 牛熊市转换时的仓位调整
    if (g.isbull == False) and (g.bond not in context.portfolio.positions):
        log.info(f'牛转熊，调整仓位，股票比例: {mkt_ratio * 100}%, 债券比例: {100 - mkt_ratio * 100}%')
        for stock in context.portfolio.positions.keys():
            target_value = context.portfolio.positions[stock].value * g.bearpercent
            order_target_value(stock, target_value)
            log.info(f'减仓个股: {stock}')
        order_target_value(g.bond, positions_value_bond)
        log.info(f'建仓债券: {positions_value_bond}')
    if (g.isbull == True) and (g.bond in context.portfolio.positions):
        log.info(f'熊转牛，调整仓位，股票比例: {mkt_ratio * 100}%, 债券比例: {100 - mkt_ratio * 100}%')
        order_target_value(g.bond, 0)
        log.info('清仓债券')
        for stock in context.portfolio.positions.keys():
            target_value = context.portfolio.positions[stock].value / g.bearpercent
            order_target_value(stock, target_value)
            log.info(f'补仓个股: {stock}')
    # 建仓新股票
    stock_position_count = len(context.portfolio.positions) - (1 if g.bond in context.portfolio.positions else 0)
    if stock_position_count < g.max_stock_count:
        value = context.portfolio.available_cash / (g.max_stock_count - stock_position_count)
        for stock in buylist:
            if (stock not in context.portfolio.positions) and check_selldate_interval(date, stock):
                order_target_value(stock, value)
                log.info(f'新增股票建仓: {stock} 目标仓位: {value}')
                if len(context.portfolio.positions) == g.max_stock_count + (1 if g.bond in context.portfolio.positions else 0):
                    break
    else:
        log.info('仓位已满，无法建仓')
# 检验某只股票距离上次卖出时间是否大于设定天数
def check_selldate_interval(date, code):
    if code in g.sell_history_df.values:
        last_date_sell = g.sell_history_df.loc[g.sell_history_df.code == code].last_date_sell.values[0]
        start = time.mktime(time.strptime(last_date_sell, '%Y-%m-%d'))
        end = time.mktime(time.strptime(date, '%Y-%m-%d'))
        count_days = int((end - start) / (24 * 60 * 60))
        if count_days < g.selldate_interval:
            log.info(f'距离最近卖出时间: {count_days}天，无法再次购买: {code}')
            return False
        log.info(f'距离最近卖出时间: {count_days}天，可以再次购买: {code}')
        return True
    log.info(f'卖出历史中无记录，可以建仓: {code}')
    return True
# 检验某只股票持有时间是否超过设定天数
def check_hold_interval(context, code, hold_interval):
    init_time = context.portfolio.positions.init_time
    count_days = (context.current_dt - init_time).days
    if count_days > hold_interval:
        log.info(f'持仓时间为: {count_days}天，可以卖出: {code}')
        return True
    log.info(f'持仓时间仅为: {
count_days}天，拒绝卖出: {code}')
    return False
# 获取前n个单位时间当时的收盘价
def get_close_price(security, n, unit='1d'):
    return attribute_history(security, n, unit, 'close')['close'][0]
# 获取牛熊信号
def get_bull_bear_signal_minute():
    nowindex = get_close_price(g.MA[0], 1, '1m')
    MAold = (attribute_history(g.MA[0], g.MA[1] - 1, '1d', 'close', True)['close'].sum() + nowindex) / g.MA[1]
    if g.isbull:
        if nowindex * (1 + g.threshold) <= MAold:
            g.isbull = False
    else:
        if nowindex > MAold * (1 + g.threshold):
            g.isbull = True
# 返回股票的中文名称
def get_stock_name(stock_code):
    if g.stocks_allnames_df.loc[g.stocks_allnames_df.index == stock_code].empty:
        return '名称未知'
    return g.stocks_allnames_df.loc[g.stocks_allnames_df.index == stock_code]['display_name'][0]
```

### 技术文档说明

1\. 策略初始化 (initialize)

  * **功能** : 初始化策略全局变量，设置牛熊市参数、交易规则、以及股票债券仓位管理等内容。

  * **配置** :

    * g.max_stock_count = 5: 设置最大持仓股票数量。

    * g.MA = ['399008.XSHE', 10]: 使用中小300指数的10日均线作为牛熊市判断依据。

    * g.bond = '511010.XSHG': 选择债券基金作为熊市下的避险资产。

2\. 开盘前运行函数 (before_market_open)

  * **功能** : 用于开盘前的预处理操作，当前未设置任何操作。

3\. 开盘时运行函数 (market_open)

  * **功能** : 判断牛熊市趋势，并根据多因子选股结果调仓，执行建仓或减仓操作。

4\. 收盘后运行函数 (after_market_close)

  * **功能** : 在收盘后执行操作，包括记录交易数据和其他收盘相关处理。

5\. 牛熊信号获取 (get_bull_bear_signal_minute)

  * **功能** : 通过中小300指数的均线判断当前市场是牛市还是熊市，以动态调整仓位。

6\. 调仓函数 (adjust_position)

  * **功能** : 根据当前市场状态和选股结果，自动调整股票和债券的仓位，实现牛熊市间的动态调仓。

  * **逻辑** :

    * 判断是否满足止盈或清仓条件，清仓不符合条件的股票。

    * 根据牛熊市状态调整股票和债券的仓位比例。

    * 如果仓位未满，建仓新的股票。

7\. 检查股票持有时间 (check_hold_interval)

  * **功能** : 检查股票是否持有超过设定的最短持仓时间，未满足条件的股票不能卖出。

8\. 检查卖出后的持仓间隔 (check_selldate_interval)

  * **功能** : 检查股票卖出后的间隔天数，未达到设定间隔时间的股票不能再次买入。

9\. 获取股票中文名称 (get_stock_name)

  * **功能** : 获取股票的中文名称，提升日志记录的可读性。

### 策略亮点

  * **牛熊市择时** : 通过技术指标动态判断牛熊市，灵活调整股票和债券的仓位比例。

  * **多因子选股** : 策略通过外部多因子选股结果进行建仓，提升股票选择的精准度。

  * **止盈与风险控制** : 设置止盈和持仓时间限制，确保投资在风险可控范围内实现收益最大化。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
