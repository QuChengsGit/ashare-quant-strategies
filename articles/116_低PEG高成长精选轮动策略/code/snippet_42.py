def get_high_growth_stocks(context, stock_codes):
    """
    根据财报数据筛选高成长、低PEG股票
    条件：
    - 当前 PE-TTM 在 (0, 30] 区间
    - 当前扣非净利润 > 0
    - 扣非净利润同比 > 0
    - 营收同比 >= 15%
    - 计算 PEG <= 1，按总市值由小到大排序
    """
    yesterday = context.previous_date                  # 上一个交易日
    day = yesterday.day                                # 记录 day 变量，处理闰年
    # === 1. 获取当期财务数据 ===
    q_current = query(
        income.code,                                   # 股票代码
        income.operating_revenue,                     # 营业收入
        indicator.adjusted_profit,                    # 扣非净利润
        valuation.pe_ratio,                           # PE-TTM
        valuation.market_cap,                         # 总市值
        valuation.circulating_market_cap              # 流通市值
    ).filter(
        income.code.in_(stock_codes),                 # 限定在候选股票池中
        valuation.pe_ratio <= 30,                     # PE-TTM <= 30
        valuation.pe_ratio > 0,                       # PE-TTM > 0，排除负数和 0
        indicator.adjusted_profit > 0                 # 当期扣非净利润为正
    )
    # 获取当前财务数据 DataFrame
    now_df = get_fundamentals(q_current, date=yesterday)
    # 若没有数据则直接返回空列表
    if now_df.empty:
        return []
    # === 2. 计算去年同期的对比日期 ===
    # 处理闰年 2 月 29 日情况，把去年对应日调整为 2 月 28 日
    if yesterday.month == 2 and yesterday.day == 29:
        day = 28
    lastyear_same_day = datetime.date(yesterday.year - 1, yesterday.month, day)
    # === 3. 获取去年同期财务数据 ===
    # 仅对当前已筛选出的 code 做进一步查询
    filtered_codes = now_df['code'].values.tolist()
    q_lastyear = query(
        income.code,
        income.operating_revenue,
        indicator.adjusted_profit,
        valuation.pe_ratio
    ).filter(
        income.code.in_(filtered_codes)
    )
    lastyear_df = get_fundamentals(q_lastyear, date=lastyear_same_day)
    # 若去年数据为空，则无法计算同比，直接返回空列表
    if lastyear_df.empty:
        return []
    # === 4. 合并当期与去年同期数据 ===
    merged_df = pd.merge(
        now_df,
        lastyear_df,
        on=['code'],
        suffixes=['', '_lastyear']
    )
    # 避免去年同期为 0 导致除零错误，只保留去年营收和利润绝对值不为 0 的样本
    merged_df = merged_df[
        (merged_df['operating_revenue_lastyear'].abs() > 0) &
        (merged_df['adjusted_profit_lastyear'].abs() > 0)
    ]
    # 若过滤后无数据，直接返回空列表
    if merged_df.empty:
        return []
    # === 5. 计算同比增速 ===
    # 营收同比增速
    merged_df['growth_operating_revenue'] = (
        (merged_df['operating_revenue'] - merged_df['operating_revenue_lastyear']) /
        merged_df['operating_revenue_lastyear'].abs()
    )
    # 扣非净利润同比增速
    merged_df['growth_adjusted_profit'] = (
        (merged_df['adjusted_profit'] - merged_df['adjusted_profit_lastyear']) /
        merged_df['adjusted_profit_lastyear'].abs()
    )
    # === 6. 计算 PEG（简化定义：PE / 利润增速*100） ===
    # 注意：growth_adjusted_profit 为比例，如 0.3 表示 30% 增长
    merged_df['peg'] = merged_df['pe_ratio'] / (merged_df['growth_adjusted_profit'] * 100)
    # === 7. 最终筛选条件 ===
    filtered_df = merged_df.loc[
        (merged_df['peg'] <= 1) &                        # PEG 小于等于 1
        (merged_df['growth_adjusted_profit'] > 0) &      # 利润同比为正
        (merged_df['growth_operating_revenue'] >= 0.15)  # 营收同比至少 15%
    ]
    # 若为空则直接返回空列表
    if filtered_df.empty:
        return []
    # 按总市值从小到大排序（偏向中小盘成长）
    filtered_df = filtered_df.sort_values(by='market_cap')
    # 提取股票代码列表
    buy_list = list(filtered_df['code'])
    return buy_list

复制
