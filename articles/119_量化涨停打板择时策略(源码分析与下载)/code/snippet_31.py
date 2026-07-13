class MyCallback(SimTraderCallback):
    """覆写回调：打印关键撮合事件"""
    def on_stock_order(self, order):
        print(f"[{now_str()}] 委托完成 代码={order.code} 成交={order.filled_volume}/{order.volume} 备注={order.remark}")
    def on_stock_trade(self, code, price, volume, order):
        print(f"[{now_str()}] 成交回报 {code} 价={price:.2f} 量={volume} 订单={order.order_id} 备注={order.remark}")
    def on_order_stock_async_response(self, order):
        print(f"[{now_str()}] 异步委托回调 已受理 订单={order.order_id} {order.code} {order.volume}@{order.price:.2f} {order.remark}")
    def on_cancel_order_stock_async_response(self, order):
        print(f"[{now_str()}] 撤单回报 订单={order.order_id} {order.code} 已撤（超时或未成）")
class StrategyRunner:
    """
    策略主控：
      - 接收行情tick，更新缓存
      - 在涨停价处进行三重过滤（队列/回封或动量）
      - 通过撮合器下单并跟踪成交/撤单
    """
    def __init__(self, code_list, limit_up_dict, buy_values):
        self.state = StrategyState()
        self.codes = code_list
        self.limit = limit_up_dict
        self.buy_values = buy_values
        self.account = SimAccount(cash=1_000_000.0)
        self.trader = SimTrader(self.account, MyCallback(), order_timeout_sec=ORDER_TIMEOUT_SEC)
        self.market = SimMarket(self.codes, self.limit)
    def on_tick(self, data, tick_ts):
        """每个tick的策略执行：仅在 09:30~10:00 时间窗内触发"""
        if not (MARKET_OPEN.time() <= tick_ts.time() <= MARKET_CLOSE.time()):
            return
        for code, sd in data.items():
            # 非池内或已下过单的股票跳过
            if (code not in self.codes) or (code in self.state.bought_list):
                continue
            # 维护该票的最近tick缓存
            self.state.data_cache[code].append(sd)
            # 仅在当前价=涨停价时考虑打板
            lim = self.limit.get(code)
            if not lim or not is_price_equal(sd['lastPrice'], lim):
                continue
            # 三重过滤：队列合理性 + （回封信号 或 25tick动量）
            ok_queue = queue_ok(sd, lim, self.buy_values)
            sig_refill = calc_refill_signal(self.state.data_cache[code], lim)
            sig_momo = calc_momo_25tick(self.state.data_cache[code], thres=MOMO_THRESHOLD)
            if not (ok_queue and (sig_refill or sig_momo)):
                continue
            # 计算下单量（按 buy_values/现价、取整到手）
            vol = calc_volume(sd['lastPrice'], self.buy_values)
            if vol < 100:
                continue
            # 以“涨停价”限价买入；下单后将该票加入“已买”以免重复下单
            _ = self.trader.order_stock_async(code, side='BUY', price=lim, volume=vol,
                                              remark='打板策略-限价涨停', ts=tick_ts)
            self.state.bought_list.add(code)
        # 对存量未完成订单执行“超时撤单”
        self.trader.cancel_if_timeout(tick_ts)
    def match_engine_step(self, data, tick_ts):
        """
        将当期“买一封单”和“封单吃单速度”同步给撮合器，驱动撮合成交
        - buy1_queue_vol：买一队列量
        - recent_fill_ratio：近期吃单比例（SimMarket里生成）
        """
        for code, sd in data.items():
            lim = self.limit.get(code)
            if not lim:
                continue
            buy1_q = sd['bidVol'][0] if (sd.get('bidVol') and len(sd['bidVol'])>0) else 0
            recent_ratio = self.market.state[code]["recent_queue_shrink"]
            recent_ratio = max(0.01, recent_ratio)  # 给最低吃单比例，避免完全“冻住”
            self.trader.try_match(code, lim, buy1_q, recent_ratio, tick_ts)
    def run(self):
        """主循环：从 09:20 生成行情到 10:00，逐秒推送tick并驱动策略/撮合"""
        tick_ts = MARKET_OPEN - timedelta(minutes=10)  # 从 09:20 开始（预热阶段）
        end_ts = MARKET_CLOSE
        print(f"[{now_str()}] 模拟启动：{tick_ts.strftime('%H:%M:%S')} → {end_ts.strftime('%H:%M:%S')}")
        step = timedelta(seconds=1)
        while tick_ts <= end_ts:
            data = self.market.gen_tick(tick_ts)  # 生成当前tick市场切片
            self.on_tick(data, tick_ts)          # 策略逻辑（可能触发下单/撤单）
            self.match_engine_step(data, tick_ts)# 传入封单与吃单比例以尝试撮合
            tick_ts += step
            time.sleep(0.005)                    # 小睡降低CPU占用（纯模拟）
        # 收盘概览
        print("\n========== 模拟收盘 ==========")
        print(f"现金余额：{self.account.cash:.2f}")
        any_pos = False
        for code, pos in self.account.positions.items():
            if pos > 0:
                any_pos = True
                print(f"{code} 持仓 {pos} 股，成本 {self.account.avg_cost[code]:.2f}")
        if not any_pos:
            print("(当日无成交/持仓)")
        print("================================\n")

复制
