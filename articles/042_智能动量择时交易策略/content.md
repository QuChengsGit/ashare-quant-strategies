# 42、智能动量择时交易策略

# 1. 策略概述

本策略通过结合动量指标、回归模型以及指数信号的多因素分析来优化交易决策。策略中对ETF进行动量评分，通过回归模型和RSRS（斜率调整标准分）信号判断市场趋势，最终决定持仓的调整和交易信号的执行。策略力求通过精确的择时和稳健的动量因子，获取长期稳定的超额收益。

# 2. 策略各部分功能代码详细技术文档说明

## 2.1 策略初始化 (initialize)

在初始化函数中，我们设置了基准指数、实时价格、滑点、交易成本等基本交易参数，并定义了股票池、动量和回归模型参数。

```python
def initialize(context):
    set_benchmark('399006.XSHE')  # 设定创业板指作为基准
    set_option('use_real_price', True)  # 使用实时价格进行交易
    set_option("avoid_future_data", True)  # 避免未来函数
    set_slippage(FixedSlippage(0.001))  # 固定滑点
    set_order_cost(OrderCost(open_tax=0, close_tax=0.000, open_commission=0.0001, close_commission=0.0001, close_today_commission=0, min_commission=0), type='fund')
    log.set_level('order', 'error')  # 设定日志等级
    g.stock_pool = [
        '510300.XSHG',  # 沪深300ETF
        '510050.XSHG',  # 上证50ETF
        '159949.XSHE',  # 创业板50
    ]
    g.stock_num = 1  # 买入评分最高的前1只ETF
    g.momentum_day = 20  # 动量因子计算窗口
    g.ref_stock = '000300.XSHG'  # 用沪深300指数作为择时计算的基础
    g.N = 18  # 计算斜率和拟合度的窗口
    g.M = 600  # 标准分的计算周期
    g.K = 8  # zscore 斜率的窗口大小
    g.biasN = 90  # 乖离动量的时间窗口
    g.lossN = 20  # 止损的周期
    g.lossFactor = 1.005  # 下跌止损的比例
    g.SwitchFactor = 1.04  # 换仓比例阈值
    g.Motion_1diff = 19  # 动量变化阈值
    g.raiser_thr = 4.8  # 股票前一天上涨比例阈值
    g.hold_stock = 'null'
    g.score_thr = -0.68  # RSRS分数买入阈值
    g.score_fall_thr = -0.43  # RSRS分数卖出阈值
    g.idex_slope_raise_thr = 12  # 指数斜率买入阈值
    g.slope_series, g.rsrs_score_history = initial_slope_series()
    g.stock_motion = initial_stock_motion(g.stock_pool)
    run_daily(my_trade_prepare, time='7:00', reference_security='000300.XSHG')
    run_daily(my_trade, time='9:30', reference_security='000300.XSHG')
    run_daily(my_sell2buy, time='9:35', reference_security='000300.XSHG')
    run_daily(check_lose, time='open', reference_security='000300.XSHG')
    run_daily(pre_hold_check, time='11:25')
    run_daily(hold_check, time='11:27')
```

## 2.2 初始数据计算 (initial_slope_series 和 initial_stock_motion)

在策略开始前，对历史数据进行计算并初始化。通过计算斜率序列和动量因子，去除回测第一天的计算偏差。

```python
def initial_slope_series():
    length = g.N + g.M + g.K
    data = attribute_history(g.ref_stock, length, '1d', ['high', 'low', 'close'])
    multe_data = [get_ols(data.low[i:i + g.N], data.high[i:i + g.N]) for i in range(length - g.N)]
    slopes = [i[1] for i in multe_data]
    r2s = [i[2] for i in multe_data]
    zscores = [(get_zscore(slopes[i + 1:i + 1 + g.M]) * r2s[i + g.M]) for i in range(g.K)]
    return slopes, zscores
def initial_stock_motion(stock_pool):
    stock_motion = {}
    for stock in stock_pool:
        motion_que = []
        data = attribute_history(stock, g.biasN + g.momentum_day + 1, '1d', ['close'])
        data = data[:-1]
        bias = (data.close / data.close.rolling(g.biasN).mean())[-g.momentum_day:]  # 乖离因子
        score = np.polyfit(np.arange(g.momentum_day), bias / bias[0], 1)[0].real * 10000  # 乖离动量拟合
        motion_que.append(score)
        stock_motion[stock] = motion_que
    return stock_motion
```

## 2.3 持仓检查 (pre_hold_check 和 hold_check)

在交易日内通过检查持仓情况，如果发现风险，及时执行止损或减仓操作。

```python
def pre_hold_check(context):
    if context.portfolio.positions:
        for stk in context.portfolio.positions:
            dt = attribute_history(stk, g.lossN + 2, '60m', ['close'])
            dt['man'] = dt.close / dt.close.rolling(g.lossN).mean()
            if dt.man[-1] < 1.0:
                log.info("盘中可能止损，卖出：{}".format(stk))
                send_message("盘中可能止损，卖出：{}".format(stk))
def hold_check(context):
    current_data = get_current_data()
    if context.portfolio.positions:
        for stk in context.portfolio.positions:
            yesterday_di = attribute_history(stk, 1, '1d', ['close'])
            dt = attribute_history(stk, g.lossN + 2, '60m', ['close'])
            dt['man'] = dt.close / dt.close.rolling(g.lossN).mean()
            if dt.man[-1] < 1.0 and current_data[stk].last_price * g.lossFactor <= yesterday_di['close'][-1]:
                stk_dict = context.portfolio.positions[stk]
                log.info('准备平仓，总仓位:{}, 可卖出：{}, '.format(stk_dict.total_amount, stk_dict.closeable_amount))
                send_message("盘中止损，卖出：{}".format(stk))
                if stk_dict.closeable_amount:
                    order_target_value(stk, 0)
                    log.info('盘中止损', stk)
                else:
                    log.info('无法止损', stk)
```

## 2.4 动量因子计算与择时信号 (get_rank 和 get_timing_signal)

通过动量因子、RSRS斜率、以及市场摆动指数等多维度因子，综合判断当前市场趋势并产生买卖信号。

```python
def get_rank(context, stock_pool):
    rank = []
    for stock in stock_pool:
        data = attribute_history(stock, g.biasN + g.momentum_day, '1d', ['close'])
        bias = (data.close / data.close.rolling(g.biasN).mean())[-g.momentum_day:]
        score = np.polyfit(np.arange(g.momentum_day), bias / bias[0], 1)[0].real * 10000  # 乖离动量拟合
        adr = 100 * (data.close[-1] - data.close[-2]) / data.close[-2]  # 股票的涨跌幅度
        raise_x = g.SwitchFactor if stock == g.hold_stock else 1
        rank.append([stock, score * raise_x, adr])
        g.stock_motion[stock].append(score)
        if len(g.stock_motion[stock]) > 5:
            g.stock_motion[stock].pop(0)
    rank = [i for i in rank if not math.isnan(i[1])]
    rank.sort(key=lambda x: x[1], reverse=True)
    return rank[0]
def get_timing_signal(context, stock):
    data = attribute_history(g.ref_stock, g.N, '1d', ['high', 'low', 'close'])
    intercept, slope, r2 = get_ols(data.low, data.high)
    g.slope_series.append(slope)
    rsrs_score = get_zscore(g.slope_series[-g.M:]) * r2
    g.rsrs_score_history.append(rsrs_score)
    rsrs_slope = get_zscore_slope(g.rsrs_score_history[-g.K:])
    idex_slope = np.polyfit(np.arange(8), data.close[-8:], 1)[0].real
    g.slope_series.pop(0)
    g.rsrs_score_history.pop(
0)
    log.info('rsrs_slope {:.3f}'.format(rsrs_slope) + ' rsrs_score {:.3f} '.format(rsrs_score) + ' idex_slope {:.3f} '.format(idex_slope))
    WR2, WR1 = WR([g.ref_stock], check_date=context.previous_date, N=21, N1=14, unit='1d', include_now=True)
    if WR1[g.ref_stock] >= 97 and WR2[g.ref_stock] >= 97:
        return "BUY"
    if rsrs_slope < 0 and rsrs_score > 0:
        return "SELL"
    if idex_slope < 0 and rsrs_slope > 0 and rsrs_score < g.score_fall_thr:
        return "SELL"
    if idex_slope > g.idex_slope_raise_thr and rsrs_slope > 0:
        return "BUY"
    if rsrs_score > g.score_thr:
        return "BUY"
    else:
        return "SELL"
```

## 2.5 交易执行与持仓调整 (my_trade_prepare, my_trade, my_sell2buy)

根据择时信号和市场动量，执行买入、卖出或保持仓位操作。

```python
def my_trade_prepare(context):
    g.check_out_list = get_rank(context, g.stock_pool)
    g.timing_signal = get_timing_signal(context, g.ref_stock)
    log.info('今日自选及择时信号:{} {}'.format(g.check_out_list[0], g.timing_signal))
    cur_stock = g.check_out_list[0]
    cur_adr = g.check_out_list[2]
    change_rate = g.stock_motion[cur_stock][-1] - g.stock_motion[cur_stock][-2]
    if change_rate > g.Motion_1diff or cur_adr > g.raiser_thr:
        g.timing_signal = 'SELL'
        log.info("由于涨跌:%f, 动量变化%0f，今日空仓" % (cur_adr, change_rate))
def my_trade(context):
    if g.timing_signal == 'SELL':
        for stock in context.portfolio.positions:
            position = context.portfolio.positions[stock]
            close_position(position)
    elif g.timing_signal == 'BUY' or g.timing_signal == 'KEEP':
        adjust_position(context, g.check_out_list)
def my_sell2buy(context):
    if g.timing_signal == 'BUY' or g.timing_signal == 'KEEP':
        buy_stocks(context, g.check_out_list)
```

# 3. 策略优化建议

  1. **超参数调优** ：根据回测数据对策略中的关键参数如K、N、M、biasN等进行调整，找到最佳参数组合。

  2. **因子扩展** ：可以尝试引入更多技术指标，如MACD、RSI等，增强策略的多维度判断能力。

  3. **风险管理** ：进一步优化止损策略和仓位管理，减少极端市场环境下的潜在损失。

  4. **增强模型架构** ：可引入机器学习模型（如SVM或LSTM）来辅助因子评分，提升择时信号的准确性。

通过上述优化和策略文档，策略能够更好地适应市场波动，优化收益表现。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
