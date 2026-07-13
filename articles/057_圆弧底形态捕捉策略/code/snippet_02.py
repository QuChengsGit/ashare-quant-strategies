from scr.pattern_detect import find_RoundingBottom
# 对每个股票的时间序列数据进行圆弧底形态检测
output: Dict = {
    code: find_RoundingBottom(
        slice_df.reset_index(level=1, drop=True), code=code
    )
    for code, slice_df in data.groupby(level='code')
}
