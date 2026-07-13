def calc_asset_max_raise(context):
    asset_values = {}
    for code in context.portfolio.positions:
        asset = g.stock_map_asset[code]
        pos = context.portfolio.positions[code]
        if asset not in asset_values:
            asset_values[asset] = pos.value
        else:
            asset_values[asset] += pos.value
    max_raise_ratio = 0
    for asset in g.rebalanced_asset_values:
        if asset in asset_values:
            ratio = asset_values[asset] / g.rebalanced_asset_values[asset]
            if ratio > max_raise_ratio:
                max_raise_ratio = ratio
    return max_raise_ratio
