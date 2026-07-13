# 91、缠论多维度买卖点量化策略

**缠论多维度买卖点量化策略** 是一种基于缠中说禅理论的自动化交易策略，通过K线、分型、笔、线段和中枢等技术分析方法，精确捕捉市场的买卖点。该策略综合使用MACD指标和缠论的核心概念来识别趋势、背驰和买卖信号，实现对股票价格走势的全方位分析，从而进行自动化交易操作。

# 策略详细介绍

  1. **策略思想** ：

     * **缠论基础** ：策略基于缠中说禅理论，使用K线、分型、笔、线段和中枢等概念，结合市场走势进行多层次分析。

     * **多维度分析** ：通过对K线的合并与非合并处理，结合分型的形成，逐步生成笔、线段，并构建中枢，最终判断市场的趋势和买卖点。

     * **自动化交易** ：策略根据分析结果，自动判断买卖时机，并执行交易操作。

  2. **关键要素** ：

     * **K线合并** ：策略允许选择是否对K线进行包含处理，以形成更为清晰的走势结构。

     * **分型与笔** ：通过对分型的分析，策略逐步生成笔，并以笔为基础构建线段。

     * **中枢构建** ：利用笔或线段构建中枢，并以此判断市场的趋势和买卖信号。

     * **买卖点识别** ：通过MACD指标对趋势进行背驰分析，识别买卖信号，并根据信号执行买卖操作。

# 策略代码与功能说明

## 1. 初始化函数 (initialize)

```python
def initialize(context):
    set_benchmark('000300.XSHG')  # 设定沪深300作为基准
    set_option('use_real_price', True)  # 开启动态复权模式(真实价格)
    log.info('初始函数开始运行且全局只运行一次')
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')  # 设置交易成本
    run_daily(before_market_open, time='every_bar', reference_security='000300.XSHG')  # 开盘前运行
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')  # 开盘时运行
    run_daily(after_market_close, time='every_bar', reference_security='000300.XSHG')  # 收盘后运行
```

  * **功能说明** : 初始化策略参数，包括基准、交易标的、交易成本，以及设定每日的运行时间和逻辑。

  * **关键逻辑** :

    * run_daily 函数用于设置策略在不同时间点执行的任务，包括开盘前、开盘时和收盘后的操作。

## 2. 开盘前运行函数 (before_market_open)

```python
def before_market_open(context):
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    g.security = '300354.XSHE'  # 设定要操作的股票
```

  * **功能说明** : 在开盘前执行的函数，主要用于设置当天操作的股票。这里设定了要操作的股票代码。

## 3. 开盘时的交易执行 (market_open)

```python
def market_open(context):
    log.info('函数运行时间(market_open):' + str(context.current_dt.time()))
    security = g.security
    df = get_bars(security, count=1, unit='1m', fields=['date','open','high','low','close'])
    if df is not None:
        for row in df:
            bar = BarData(datetime=row[0], high_price=row[2], low_price=row[3], close_price=row[4])
            chan.on_bar(bar)
```

  * **功能说明** : 开盘时运行的函数，获取当前时刻的K线数据，并将其传递给策略的核心算法 Chan_Strategy 进行分析。

  * **关键逻辑** :

    * get_bars 函数用于获取指定股票的历史K线数据， chan.on_bar(bar) 用于将K线数据传递给策略进行处理。

## 4. 收盘后运行函数 (after_market_close)

```python
def after_market_close(context):
    log.info('函数运行时间(after_market_close):' + str(context.current_dt.time()))
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：' + str(_trade))
    log.info('一天结束')
    log.info('##############################################################')
```

  * **功能说明** : 收盘后运行的函数，用于记录当天的交易情况，并打印交易日志。

  * **关键逻辑** :

    * get_trades 函数用于获取当天的所有交易记录，便于后续分析与复盘。

## 5. 缠论策略核心算法 (Chan_Strategy)

```python
class Chan_Strategy:
    def __init__(self, include=True, build_pivot=False):
        self.k_list = []
        self.chan_k_list = []
        self.fx_list = []
        self.stroke_list = []
        self.line_list = []
        self.line_index = {}
        self.line_feature = []
        self.s_feature = []
        self.x_feature = []
        self.pivot_list = []
        self.trend_list = []
        self.buy_list = []
        self.x_buy_list = []
        self.sell_list = []
        self.x_sell_list = []
        self.macd = {}
    def on_bar(self, bar: BarData):
        self.on_period(bar)
    def on_period(self, bar: BarData):
        self.k_list.append(bar)
        if self.include:
            self.on_process_k_include(bar)
        else:
            self.on_process_k_no_include(bar)
    # 其他方法如 on_process_k_include, on_process_fx, on_stroke 等...
```

  * **功能说明** : 这是缠论策略的核心部分，包含了缠论的各种概念实现，如K线合并、分型、笔、线段、中枢等。通过这些分析方法，策略能够识别买卖点并执行交易。

  * **关键逻辑** :

    * on_bar 函数用于处理每一个K线数据。

    * on_process_k_include 和 on_process_k_no_include 负责处理K线的合并与非合并逻辑。

    * on_stroke, on_line, on_pivot, on_trend 等函数用于逐步构建缠论中的笔、线段和中枢，并最终识别出买卖信号。

### 总结

**缠论多维度买卖点量化策略** 是一种基于缠论理论的复杂交易策略。它通过多维度的技术分析，精确识别市场趋势和买卖点，并通过自动化交易执行。这一策略适用于对缠论有深入理解并希望将其应用于量化交易中的投资者。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
