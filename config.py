# config.py
import numpy as np

# 创建更稀疏的通勤矩阵
def create_commute_matrix(size):
    """创建随机通勤矩阵"""
    matrix = np.zeros((size, size))
    for i in range(size):
        # 每个建筑平均5个连接
        connections = np.random.choice(size, size=min(5, size), replace=False)
        for j in connections:
            if i != j:
                # 较低的通勤权重
                matrix[i][j] = max(0.001, min(0.05, np.random.normal(0.02, 0.01)))
    return matrix

# 假设有5000个建筑
COMMUTE_MATRIX = create_commute_matrix(5000)

SIMULATION_PARAMS = {
    'usb_per_capita': 1,          # 降低人均USB数量
    'carry_rate': 0.8,             # 大幅降低携带率
    'spread_intensity': 0.7,        # 降低传播强度因子
    'cleanup_rate': 0.05,            # 提高清理率
    'cleanup_interval': 7,          # 缩短清理周期
    'commute_matrix': COMMUTE_MATRIX,
    'max_steps': 100
}
