# 获取收盘价
def get_close_price(code, n, unit='
1d'):
    return attribute_history(code, n, unit, 'close')['close'][0]
# 获取增长率
def get_growth_rate(days, code):
    try:
        price_period = attribute_history(code, days, '1d', 'close', False)['close'][0]
        pricenow = get_close_price(code, 1, '1m')
        if not math.isnan(pricenow) and not math.isnan(price_period) and price_period != 0:
            return pricenow / price_period
        else:
            return 100
    except Exception as e:
        print(f"Error calculating growth rate for stock {code}: {e}")
        return 100
# 定义平仓，卖出指定持仓
def close_position(code):
    order = order_target_value(code, 0)
    if order is not None and order.status == OrderStatus.held:
        g.sold_stock[code] = 0

复制
