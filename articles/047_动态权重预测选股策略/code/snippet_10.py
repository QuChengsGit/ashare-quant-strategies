# 读取研究环境的预测结果
df = pd.read_csv(BytesIO(read_file("predict.csv")), index_col=0)
df2 = pd.read_csv(BytesIO(read_file("target.csv")), index_col=0)
# 计算预测误差的绝对值并进行平滑处理
mae_df = (df - df2).abs().rolling(10).mean()
mae_df = mae_df.shift(2)
# 选取预测值排名靠前的股票
top = 5  # 选取的股票数量
indexlist = df['2022-08':].index.tolist()
dict_position = {}
for x in indexlist:
    temp = df.loc[x].sort_values(ascending=False).head(top).index.tolist()
    dict_position[x] = temp
