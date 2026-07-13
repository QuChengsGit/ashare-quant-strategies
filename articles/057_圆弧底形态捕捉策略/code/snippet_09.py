from scr.plotting import view_gride_chart
# 设置图表显示参数
cols: int = 2
size: int = len(codes)
rows: int = size // 2 + 1 if size % 2 else size / 2
# 绘制符合圆弧底形态的股票的价格走势图
view_gride_chart(codes, data, rows=rows, cols=cols, figsize=(20, rows * 5 + 5))
# 技术说明：
# 使用 `view_gride_chart` 函数将符合圆弧底形态的股票价格走势可视化。通过设置图表的行数和列数，使得多只股票的走势能够在一个
# 图表中网格显示，以便进行形态验证和进一步分析。

复制
