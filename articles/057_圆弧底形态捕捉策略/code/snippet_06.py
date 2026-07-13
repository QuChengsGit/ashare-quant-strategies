from scr.pattern_detect import find_RoundingBottom
# 对每个股票的时间序列数据进行圆弧底形态检测
output: Dict = {
    code: find_RoundingBottom(
        slice_df.reset_index(level=1, drop=True), code=code
    )
    for code, slice_df in data.groupby(level='code')
}
output_df: pd.DataFrame = pd.DataFrame(output, index=['是否圆弧底', '是否符合买入点']).T
output_df.head()
# 技术说明：
# 使用 `find_RoundingBottom` 函数检测每只股票的价格序列是否形成圆弧底形态。检测结果存储在字典 `output` 中，
# 然后将其转换为 DataFrame `output_df`，该 DataFrame 包含了每只股票的形态检测结果。
