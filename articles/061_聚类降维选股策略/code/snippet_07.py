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

复制
