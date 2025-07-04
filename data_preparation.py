# data_preparation.py
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, Polygon
import random
import os

# 创建数据目录
os.makedirs('data', exist_ok=True)

def generate_neighbourhood_data():
    print("生成模拟街区数据...")
    num_buildings = 5000
    lat_min, lat_max = 37.75, 37.78
    lon_min, lon_max = -122.42, -122.40
    
    # 创建建筑物数据
    buildings = []
    entry_points = []
    building_ids = []
    areas = []
    populations = []
    
    for i in range(num_buildings):
        center_lon = random.uniform(lon_min, lon_max)
        center_lat = random.uniform(lat_min, lat_max)
        
        # 创建简单的矩形建筑物
        building = Polygon([
            (center_lon - 0.0001, center_lat - 0.00005),
            (center_lon + 0.0001, center_lat - 0.00005),
            (center_lon + 0.0001, center_lat + 0.00005),
            (center_lon - 0.0001, center_lat + 0.00005)
        ])
        
        # 创建入口点（建筑物前门）
        entry_point = Point(center_lon + 0.0001, center_lat)  # 建筑物右侧
        
        # 计算面积和人口密度
        area = random.uniform(100, 500)  # 固定面积范围
        population = max(1, int(area / 100))
        
        # 收集数据
        buildings.append(building)
        entry_points.append(entry_point)
        building_ids.append(i)
        areas.append(area)
        populations.append(population)
    
    # 创建GeoDataFrame - 主几何列为建筑物多边形
    gdf = gpd.GeoDataFrame({
        'building_id': building_ids,
        'area': areas,
        'population': populations,
        'entry_point': entry_points  # 作为普通列存储点几何
    }, geometry=buildings, crs="EPSG:4326")
    
    # 添加USB相关字段
    gdf['infected_usb'] = 0  # 感染USB数量
    gdf['total_usb'] = (gdf['population'] * 1.0).astype(int)  # 人均1.0个USB
    gdf.loc[gdf['total_usb'] == 0, 'total_usb'] = 1  # 确保至少有一个USB
    
    # 对人口较多的建筑增加USB数量
    large_buildings = gdf[gdf['population'] > 20].index
    gdf.loc[large_buildings, 'total_usb'] = (gdf.loc[large_buildings, 'population'] * 1.5).astype(int)
    
    # 保留感染时间和来源字段
    gdf['infection_time'] = -1  # 获得物品时间
    gdf['source'] = -1  # 传播来源，使用-1表示无来源
    
    # 保存为GeoJSON - 只包含主几何列
    output_path = 'data/neighbourhood.geojson'
    gdf.to_file(output_path, driver='GeoJSON')
    print(f"已保存街区数据到: {output_path}")
    
    return gdf

if __name__ == "__main__":
    generate_neighbourhood_data()