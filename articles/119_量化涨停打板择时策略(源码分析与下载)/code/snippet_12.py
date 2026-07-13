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
