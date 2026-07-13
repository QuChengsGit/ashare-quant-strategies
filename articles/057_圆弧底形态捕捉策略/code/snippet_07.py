# 获取符合圆弧底形态的股票
rounding_bottom: pd.DataFrame = output_df.query("是否圆弧底==True")
# 符合圆弧底形态的股票代码
codes: List = rounding_bottom.index.tolist()
# 技术说明：
# 使用查询过滤的方法，从检测结果中筛选出符合圆弧底形态的股票代码，保存在列表 `codes` 中。

复制
