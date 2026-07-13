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
