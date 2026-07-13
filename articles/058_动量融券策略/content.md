# 58、动量融券策略

### 策略介绍：

**动量融券策略** 是一种基于市场动量的量化融券策略。该策略通过分析全市场中可融券股票的价格波动情况，选择波动较大的股票进行融券卖出，以期在价格回调时获利。策略利用融资融券机制，在市场波动较大的情况下，通过融券卖出高波动率的股票，力求捕捉短期内的价格回落机会。

### 核心代码及技术文档说明

1\. 初始化函数

```python
from jqdata import *
def initialize(context):
    set_benchmark('000300.XSHG')  # 设定基准指数为沪深300
    set_option('use_real_price', True)  # 启用动态复权模式，确保使用真实价格进行交易
    log.info('初始函数开始运行且全局只运行一次')
    # 设置融资融券账户配置
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.cash, type='stock_margin')])
    # 融资融券相关参数设定
    set_option('margincash_interest_rate', 0.08)  # 设定融资利率为年化8%
    set_option('margincash_margin_rate', 1.5)  # 设定融资保证金比率为150%
    set_option('marginsec_interest_rate', 0.10)  # 设定融券利率为年化10%
    set_option('marginsec_margin_rate', 1.5)  # 设定融券保证金比率为150%
    # 设置交易成本与滑点
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    set_slippage(PriceRelatedSlippage(0.00246), type='stock')  # 设置滑点为千分之二点四六
    # 设定运行函数
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(clear_close, time='14:55', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
```

技术说明：

  * **初始化** ：设置策略的基准指数、动态复权模式、融资融券账户配置，以及交易成本和滑点。通过设定每日的运行函数，实现策略的自动化交易流程。

  * **融资融券配置** ：设置融资和融券的利率及保证金比率，确保策略在实际操作中符合市场规则。

2\. 开盘前准备

```python
def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    g.buylist0 = []
# 技术说明：
# 在开盘前的准备阶段，初始化当日的股票买卖列表 `g.buylist0`，为后续的交易决策做准备。
```

3\. 市场开盘与融券操作

```python
def market_open(context):
    log.info('开始还券...')
    rq_stock = context.portfolio.short_positions
    # 还券操作
    for stock in rq_stock:
        current_price = get_bars(stock, count=1, unit='5m', fields=['close'], include_now=True)['close'][-1]
        log.info("买券还券: %s" % [stock, current_price, rq_stock[stock].total_amount])
        marginsec_close(stock, rq_stock[stock].total_amount)
# 技术说明：
# 市场开盘后，策略会首先执行还券操作，即对前一交易日融券卖出的股票进行买入并还券，以清算头寸。
```

4\. 尾盘融券卖出操作

```python
def clear_close(context):
    log.info('开始融券卖出...')
    # 获取全市场可融券标的
    security = get_marginsec_stocks(date=context.current_dt)
    current_data = get_current_data()
    zf_dict = {}
    for s in security:
        cc = get_bars(s, count=2, unit='1d', fields=['high', 'low', 'close'], include_now=True)
        if not current_data[s].paused and len(cc['close']) == 2:
            zf = (cc['high'][-1] - cc['low'][-1]) / cc['close'][0] * 100
            if (cc['high'][-1] - cc['low'][-1]) / (current_data[s].high_limit - cc['close'][0]) > 1.5:
                zf_dict[s] = zf
    # 对波动率进行排序，选择波动率最高的股票进行融券卖出
    dm = sorted(zf_dict.items(), key=lambda x: x[1], reverse=True)
    g.buylist0 = [s[0] for s in dm][:10]
    log.info('融券卖出: %s' % g.buylist0)
    if g.buylist0:
        position_per_money = context.portfolio.total_value / len(g.buylist0)
        for stock in g.buylist0:
            current_price = get_bars(stock, count=1, unit='5m', fields=['close'], include_now=True)['close'][-1]
            position_per_money_n = int(position_per_money / current_price / 100) * 100
            log.info("融券卖出: %s" % [stock, current_price, position_per_money_n])
            marginsec_open(stock, position_per_money_n)
# 技术说明：
# 在尾盘时，策略会对全市场可融券标的进行波动率筛选，选择波动率较大的股票进行融券卖出。卖出数量根据总资产按比例分配。
```

5\. 收盘后账户信息查看

```python
def after_market_close(context):
    p = context.portfolio.subportfolios[0]
    log.info('-' * 60)
    log.info('查看融资融券账户相关信息：')
    log.info('总资产：', p.total_value)
    log.info('净资产：', p.net_value)
    log.info('总负债：', p.total_liability)
    log.info('融资负债：', p.cash_liability)
    log.info('融券负债：', p.sec_liability)
    log.info('利息总负债：', p.interest)
    log.info('可用保证金：', p.available_margin)
    log.info('维持担保比例：', p.maintenance_margin_rate)
    log.info('账户所属类型：', p.type)
    log.info('##############################################################')
# 技术说明：
# 在收盘后，策略会输出融资融券账户的详细信息，包括总资产、净资产、负债情况等，以便监控账户的整体风险状况。
```

### 策略优势：

  * **利用波动率进行筛选** ：通过波动率筛选，策略能够有效捕捉市场短期内可能出现的回调机会。

  * **融券操作的灵活性** ：利用融资融券机制，可以在市场下行时通过融券操作获利，实现多空结合的投资策略。

  * **自动化交易流程** ：策略自动化执行从筛选、交易到收盘后的所有环节，减少人工干预，提升执行效率。

### 总结：

**动量融券策略** 利用市场的波动特性，结合融券操作，在市场短期波动中捕捉下跌机会。策略适合在波动性较高的市场环境中操作，尤其是在市场面临不确定性或调整压力时，通过融券卖出高波动股票获得收益。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
