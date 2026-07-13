# 61、聚类降维选股策略

### 策略介绍

**聚类降维选股策略** 是一种结合机器学习技术和量化分析的选股策略。该策略通过 t-SNE 降维和 K-means 聚类算法，从大盘中筛选出潜力股，进一步依据市值和盈利指标筛选优质股票。策略利用股票的历史收益率数据进行降维处理，确保在多维特征空间内识别出具有相似特征的股票群体。通过聚类分析，确定每个聚类的中心样本，并以此作为代表性股票进行投资。

### 核心代码及技术文档说明

1\. 数据准备与股票筛选

```python
from jqdata import *
import datetime
import numpy as np
def get_stock(stockPool, begin_date):
    # 选择股票池
    if stockPool == 'AA':
        stockList = get_index_stocks('000985.XSHG', begin_date)
        stockList = [stock for stock in stockList if not stock.startswith(('3', '68', '4', '8'))]
    # 剔除ST股、停牌、新股及退市股票
    st_data = get_extras('is_st', stockList, count=1, end_date=begin_date)
    stockList = [stock for stock in stockList if not st_data[stock][0]]
    stockList = delect_stop(stockList, begin_date)
    return stockList
# 移除上市不足n天的股票
def delect_stop(stocks, beginDate, n=365):
    stockList = []
    beginDate = datetime.datetime.strptime(beginDate, "%Y-%m-%d")
    for stock in stocks:
        start_date = get_security_info(stock).start_date
        if start_date < (beginDate - datetime.timedelta(days=n)).date():
            stockList.append(stock)
    return stockList
# 获取股票池
current_date = datetime.datetime.now()
current_time = current_date.strftime("%Y-%m-%d")
stockList = get_stock('AA', current_time)
```

技术说明：

  * **股票筛选** ：首先定义了获取股票池的函数，通过剔除ST股、停牌股票、新股及退市股票等操作，确保筛选出的股票池质量较高。

2\. 数据处理与降维

```python
_end_date = current_date + datetime.timedelta(-2)
_end_date = _end_date.strftime("%Y-%m-%d")
DATA = []
for i in stockList:
    df = get_price(i, frequency='1d', start_date='2023-01-01', end_date=_end_date, fields=['close'])
    df['returns'] = df['close'].pct_change() * 100
    df = df.dropna()
    returns_array = df['returns'].values
    DATA.append(returns_array)
DATA = np.array(DATA)
# 使用 t-SNE 进行降维
from sklearn.manifold import TSNE
tsne = TSNE(n_components=2, random_state=42)
embedded_data = tsne.fit_transform(DATA)
# t-SNE 降维后的可视化
import matplotlib.pyplot as plt
plt.scatter(embedded_data[:, 0], embedded_data[:, 1], marker='.', alpha=0.5)
plt.title('t-SNE Visualization')
plt.show()
```

技术说明：

  * **数据处理** ：将每只股票的历史收盘价计算收益率，并进行处理，将其转换为适合机器学习模型的数据格式。

  * **t-SNE 降维** ：利用 t-SNE 技术将高维的收益率数据降维到2维，便于后续聚类操作和可视化分析。

3\. 聚类分析与选股

```python
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
# 使用 K-Means 聚类
num_clusters = 10
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
labels = kmeans.fit_predict(embedded_data)
# 获取每个簇的中心样本
cluster_centers = kmeans.cluster_centers_
center_sample_indices, _ = pairwise_distances_argmin_min(cluster_centers, embedded_data)
# 可视化聚类结果
plt.scatter(embedded_data[:, 0], embedded_data[:, 1], c=labels, cmap='viridis', alpha=0.5)
plt.scatter(cluster_centers[:, 0], cluster_centers[:, 1], marker='X', s=200, color='red', label='Centroids')
for i, index in enumerate(center_sample_indices):
    plt.text(cluster_centers[i, 0], cluster_centers[i, 1], str(index), fontsize=8, ha='center', va='center', color='black')
plt.title('K-Means Clustering with t-SNE Visualization')
plt.legend()
plt.show()
```

技术说明：

  * **K-Means 聚类** ：对降维后的数据进行聚类分析，确定不同簇的中心样本，并将其作为代表性股票。

  * **聚类可视化** ：通过散点图可视化不同聚类，帮助识别每个簇的代表性股票。

4\. 代表性股票选取

```python
# 获取一只股票的名称和行业信息
def get_stock_name(code):
    return get_security_info(code).display_name
def get_stock_industry(code):
    return get_industry(code, date=None)['jq_l2']['industry_name']
LIST = []
industry = []
name = []
for i in center_sample_indices:
    LIST.append(stockList[i])
    industry.append(get_industry(stockList[i], date=_end_date)[stockList[i]]['jq_l2']['industry_name'])
    name.append(get_security_info(stockList[i]).display_name)
# 获取市值和盈利能力作为最终筛选条件
q = query(valuation.code, valuation.circulating_market_cap, indicator.eps).filter(
    valuation.code.in_(LIST)).order_by(valuation.circulating_market_cap.asc())
df = get_fundamentals(q)
df['name'] = name
df['industry'] = industry
print(df)
```

技术说明：

  * **代表性股票信息提取** ：通过中心样本的股票代码获取其名称和行业信息，进一步结合市值和盈利能力等财务指标进行筛选，确定最终投资组合。

### 策略优势：

  * **结合机器学习的选股策略** ：通过 t-SNE 和 K-Means 等机器学习技术，从大规模数据中提取信息，提高选股的精准度。

  * **多维数据分析** ：利用多维数据降维技术，将复杂的历史数据简化为易于分析的二维数据，并进行聚类分析，有助于发掘潜在的市场机会。

  * **动态调整与风险控制** ：策略能够动态筛选具有良好历史表现的股票，并通过聚类分析有效分散风险。

### 总结：

**聚类降维选股策略** 提供了一种新的选股思路，通过机器学习技术和量化分析的结合，能够从复杂的数据中提取出具有潜力的股票。该策略特别适合对数据敏感并希望利用机器学习技术优化投资组合的量化投资者。在市场波动性较大的环境下，该策略有助于识别并投资于表现较为稳定且具有潜力的股票。

免责声明

本文所发布的所有内容仅供参考和技术研究，所提供的投资策略、分析和观点并不构成任何形式的投资建议。投资涉及风险，读者应根据自身的投资目标、风险承受能力及财务状况，独立做出决策。我们不对任何因文章内容而产生的投资损失或其他风险后果负责。请在投资前咨询专业的财务顾问或投资专家。
