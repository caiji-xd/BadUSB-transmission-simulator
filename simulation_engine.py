# simulation_engine.py
import networkx as nx
import numpy as np
from shapely import wkt
import pandas as pd

class SpreadSimulator:
    def __init__(self, gdf, params):
        # 预处理：确保entry_point是几何对象
        if isinstance(gdf['entry_point'].iloc[0], str):
            gdf = gdf.copy()
            gdf['entry_point'] = gdf['entry_point'].apply(wkt.loads)
        
        # 初始化USB相关属性
        gdf = gdf.copy()
        if 'infected_usb' not in gdf.columns:
            gdf['infected_usb'] = 0
        if 'total_usb' not in gdf.columns:
            # 计算总USB数量：人口 × 人均USB数
            gdf['total_usb'] = (gdf['population'] * params['usb_per_capita']).astype(int)
        
        self.gdf = gdf
        self.params = params
        self.build_behavior_network()
        
    def build_behavior_network(self):
        """构建基于人员流动的行为网络"""
        # 如果有预设的通勤矩阵，优先使用
        if 'commute_matrix' in self.params:
            commute_matrix = self.params['commute_matrix']
            # 转换为权重图（取对数降低强度）
            self.G = nx.from_numpy_array(np.log1p(commute_matrix))
        else:
            # 创建更稀疏的网络
            n = len(self.gdf)
            self.G = nx.Graph()
            
            # 添加节点
            for i in range(n):
                self.G.add_node(i)
            
            # 随机添加边（每个节点平均5个连接）
            for i in range(n):
                # 随机选择邻居
                neighbors = np.random.choice(n, size=min(5, n-1), replace=False)
                for j in neighbors:
                    if i != j:
                        # 随机权重（0.01-0.1）
                        weight = np.random.uniform(0.01, 0.1)
                        self.G.add_edge(i, j, weight=weight)
        
        # 添加节点属性
        for idx in self.G.nodes:
            row = self.gdf.iloc[idx]
            self.G.nodes[idx].update({
                'building_id': row['building_id'],
                'geometry': row['geometry'],
                'entry_point': row['entry_point'],
                'population': row['population'],
                'infected_usb': row['infected_usb'],
                'total_usb': row['total_usb'],
                'infection_time': row.get('infection_time', -1),
                'source': row.get('source', -1)
            })
    
    def run_step(self, step):
        """执行单步传播，返回新感染事件列表"""
        new_infections = []
        active_nodes = [n for n in self.G.nodes if self.G.nodes[n]['infected_usb'] > 0]
        
        # USB清理机制（定期清理）
        if 'cleanup_interval' in self.params and step % self.params['cleanup_interval'] == 0:
            for node in self.G.nodes:
                node_data = self.G.nodes[node]
                if node_data['infected_usb'] > 0:
                    # 二项分布模拟清理过程
                    cleaned = np.random.binomial(
                        node_data['infected_usb'],
                        self.params['cleanup_rate']
                    )
                    node_data['infected_usb'] = max(0, node_data['infected_usb'] - cleaned)
        
        # 传播机制 - 限制传播强度
        for src in active_nodes:
            src_data = self.G.nodes[src]
            if src_data['infected_usb'] <= 0:
                continue
                
            # 计算源节点感染比例
            src_infection_ratio = src_data['infected_usb'] / max(1, src_data['total_usb'])
            
            # 限制每个源节点每天最多传播5个邻居
            neighbors = list(self.G.neighbors(src))
            np.random.shuffle(neighbors)
            max_neighbors = min(5, len(neighbors))
            
            for neighbor in neighbors[:max_neighbors]:
                dst_data = self.G.nodes[neighbor]
                
                # 跳过无USB或已全感染的节点
                if dst_data['total_usb'] == 0 or dst_data['infected_usb'] >= dst_data['total_usb']:
                    continue
                
                # 计算传播强度 = 边权重 × 携带率 × 感染比例 × 传播强度因子
                edge_weight = self.G[src][neighbor].get('weight', 0.01)
                carry_prob = edge_weight * self.params['carry_rate']
                
                # 添加每日衰减因子
                time_factor = max(0.1, 1.0 - (step * 0.02))
                
                infection_intensity = carry_prob * src_infection_ratio * self.params['spread_intensity'] * time_factor
                
                # 计算可感染设备数
                max_infectable = dst_data['total_usb'] - dst_data['infected_usb']
                
                # 使用二项分布更合理（泊松分布容易产生大值）
                new_infections_count = np.random.binomial(
                    max_infectable, 
                    min(0.5, infection_intensity)
                )
                
                if new_infections_count > 0:
                    # 更新目标节点状态
                    dst_data['infected_usb'] += new_infections_count
                    dst_data['infection_time'] = step
                    dst_data['source'] = src
                    new_infections.append((src, neighbor))
        
        return new_infections
