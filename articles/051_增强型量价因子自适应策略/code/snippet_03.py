import qlib
from qlib.workflow import R  # 实验记录管理器
from qlib.constant import REG_CN
from qlib.workflow.record_temp import SignalRecord, SigAnaRecord
# 初始化Qlib
qlib.init(provider_uri="qlib_etf_data", region=REG_CN)
# 加载ETF行业数据
industry_etf: pd.DataFrame = pd.read_csv(
    '../行业有效量价因子/qlib_etf_data/instruments/industry_etf.txt',
    delimiter='\t', header=None, parse_dates=[1, 2]
)
industry_etf.columns = ['symbol', 'begin_dt', 'end_dt']
# 数据可视化分析
industry_etf["begin_dt"].dt.year.value_counts().sort_index().plot.bar()
industry_etf["begin_dt"].dt.year.value_counts().div(
    len(industry_etf)
).sort_index().cumsum().plot(marker='o')
plt.show()
