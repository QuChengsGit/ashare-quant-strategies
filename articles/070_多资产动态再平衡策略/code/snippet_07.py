def init_stock_map_asset(pool):
    stock_map_asset = {}
    for asset in pool:
        for stocks in pool[asset]['codes']:
            for code in stocks:
                stock_map_asset[code] = asset
    return stock_map_asset

复制
