fields=["open", "high", "low", "close", "volume", "amount"],
)
# 数据预处理：转换单位与设置初始因子
benchmark['volume'] *= 100
benchmark['amount'] *= 1000
benchmark['factor'] = 1
# 合并数据并保存为CSV文件
data_all: pd.DataFrame = pd.concat((etf_price, benchmark))
