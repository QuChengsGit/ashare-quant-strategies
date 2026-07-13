# ==============================
# 模拟撮合/回调（最小可用撮合内核）
# ==============================
class SimOrder:
    """模拟的订单对象：仅支持限价买入"""
    def __init__(self, order_id, code, side, price, volume, remark, ts):
        self.order_id = order_id    # 订单编号（自增）
        self.code = code            # 股票代码
        self.side = side            # BUY/SELL（本策略仅用BUY）
        self.price = price          # 限价（策略里=涨停价）
        self.volume = volume        # 委托股数
        self.remark = remark        # 备注（方便日志）
        self.created_at = ts        # 下单时间戳（datetime）
        self.filled_volume = 0      # 已成交数量
        self.canceled = False       # 是否已撤
        self.done = False           # 是否已完成（完全成交）
class SimAccount:
    """模拟账户：仅记录现金+持仓+均价，并在成交时更新"""
    def __init__(self, cash=1_000_000.0):
        self.cash = cash
        self.positions = defaultdict(int)   # code -> 持股数
        self.avg_cost = defaultdict(float)  # code -> 持仓均价
        self.lock = threading.Lock()        # 线程安全（撮合回调与主循环可能并行）
    def on_trade(self, code, price, vol, side):
        """成交回写账户：买入扣现金、更新均价；（若有卖出则加现金/减仓）"""
        with self.lock:
            if side == 'BUY':
                cost = price * vol
                self.cash -= cost
                pos = self.positions[code]
                new_pos = pos + vol
                # 新均价 = (旧成本 + 本次成本) / 新持仓
                self.avg_cost[code] = (self.avg_cost[code] * pos + cost) / new_pos if pos > 0 else price
                self.positions[code] = new_pos
            else:
                # 这里未使用SELL，但保留逻辑以便扩展
                self.cash += price * vol
                self.positions[code] -= vol
                if self.positions[code] <= 0:
                    self.positions[code] = 0
                    self.avg_cost[code] = 0.0
class SimTraderCallback:
    """
    “柜台”回调接口（空实现），外部策略可继承覆写以打印日志等
    - on_order_stock_async_response：异步接单回报
    - on_stock_trade：逐笔成交回报
    - on_stock_order：订单完成（全部成交）可视作委托完成通知
    - on_cancel_order_stock_async_response：撤单结果
    """
    def on_stock_order(self, order): pass
    def on_stock_trade(self, code, price, volume, order): pass
    def on_order_stock_async_response(self, order): pass
    def on_cancel_order_stock_async_response(self, order): pass
class SimTrader:
    """
    极简撮合器：
    - 仅撮合“买入@涨停价”的限价单；
    - 成交量由“买一队列量 * 近期吃单比例”上限决定；
    - 按到达顺序遍历订单分配可成交量；
    - 订单超时未完全成交会被撤销（ORDER_TIMEOUT_SEC）。
    """
    def __init__(self, account: SimAccount, cb: SimTraderCallback, order_timeout_sec=ORDER_TIMEOUT_SEC):
        self.acc = account
        self.cb = cb
        self.order_timeout = order_timeout_sec
        self._id = 0
        self.orders = {}             # oid -> SimOrder
        self.lock = threading.Lock() # 下单/访问订单字典的并发保护
    def order_stock_async(self, code, side, price, volume, remark, ts):
        """异步下单：分配订单号，写入订单簿，并回调“已受理”"""
        with self.lock:
            self._id += 1
            oid = self._id
            od = SimOrder(oid, code, side, price, volume, remark, ts)
            self.orders[oid] = od
        if self.cb:
            self.cb.on_order_stock_async_response(od)
        return oid
    def cancel_if_timeout(self, now_ts):
        """
        撤单扫描：若订单自创建起超过 order_timeout 仍未完成，则设置为已撤，并发回撤单回报
        - 模拟真实环境中“排队超时撤单”的风险控制动作
        """
        for od in list(self.orders.values()):
            if od.done or od.canceled:
                continue
            if (now_ts - od.created_at).total_seconds() >= self.order_timeout:
                od.canceled = True
                if self.cb:
                    self.cb.on_cancel_order_stock_async_response(od)
    def try_match(self, code, limit_price, buy1_queue_vol, recent_fill_ratio, tick_ts):
        """
        撮合：在当前tick内，对所有“code 且 限价=涨停价 且 未撤/未完”的BUY订单进行匹配
        - can_fill_total = buy1_queue_vol * recent_fill_ratio
        - 逐单分配：每单能吃多少吃多少，直到“可吃总量”耗尽
        """
        # 过滤出可参与本次撮合的订单
        live = [od for od in self.orders.values()
                if (od.code == code and (not od.done) and (not od.canceled)
                    and od.side == 'BUY' and is_price_equal(od.price, limit_price))]
        if not live:
            return
        # 本tick可消化的总量（由封单量与近期吃单速度决定）
        can_fill_total = int(max(0, recent_fill_ratio * buy1_queue_vol))
        for od in live:
            if can_fill_total <= 0:
                break
            want = od.volume - od.filled_volume
            if want <= 0:
                od.done = True
                continue
            # 实际成交量 = min(订单剩余需求, 本tick剩余可吃量)
            fill = min(want, can_fill_total)
            if fill > 0:
                od.filled_volume += fill
                can_fill_total -= fill
                # 写回账户与回调成交
                self.acc.on_trade(od.code, limit_price, fill, od.side)
                if self.cb:
                    self.cb.on_stock_trade(od.code, limit_price, fill, od)
                # 若订单完全成交，回调“委托完成”
                if od.filled_volume >= od.volume:
                    od.done = True
                    if self.cb:
                        self.cb.on_stock_order(od)
