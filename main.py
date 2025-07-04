# main.py
import geopandas as gpd
import numpy as np
from simulation_engine import SpreadSimulator
from config import SIMULATION_PARAMS
import os

def run_simulation():
    # 创建结果目录
    os.makedirs('data/daily_results', exist_ok=True)
    
    # 加载街区数据
    gdf = gpd.read_file('data/neighbourhood.geojson')
    print(f"已加载 {len(gdf)} 个建筑物数据")
    
    # 初始化模拟器
    simulator = SpreadSimulator(gdf, SIMULATION_PARAMS)
    
    # 设置初始感染点 - 30个感染USB
    start_node = np.random.choice(len(gdf))
    
    # 确保初始感染点有足够USB
    min_usb = 30
    if simulator.G.nodes[start_node]['total_usb'] < min_usb:
        # 如果总USB不足30，设置为全部感染
        simulator.G.nodes[start_node]['infected_usb'] = simulator.G.nodes[start_node]['total_usb']
    else:
        # 否则感染30个USB
        simulator.G.nodes[start_node]['infected_usb'] = min_usb
    
    simulator.G.nodes[start_node]['infection_time'] = 0
    simulator.G.nodes[start_node]['source'] = -1
    print(f"初始感染点: 建筑物 {start_node} (感染USB: {simulator.G.nodes[start_node]['infected_usb']}/{simulator.G.nodes[start_node]['total_usb']})")
    
    # 保存第0天状态
    save_daily_result(simulator, 0)
    
    # 运行模拟，天数这里也要改
    max_steps = 100
    print(f"开始传播模拟 (共 {max_steps} 天)...")
    
    for step in range(1, max_steps + 1):
        new_infections = simulator.run_step(step - 1)  # 传入前一天作为参数
        
        # 计算当前感染状态
        infected_buildings = sum(1 for n in simulator.G.nodes if simulator.G.nodes[n]['infected_usb'] > 0)
        total_infected_usb = sum(simulator.G.nodes[n]['infected_usb'] for n in simulator.G.nodes)
        
        if step % 5 == 0 or step == max_steps:
            print(f"Day {step}: 新增传播事件 {len(new_infections)} | "
                  f"感染建筑 {infected_buildings}/{len(gdf)} | "
                  f"感染USB总数 {total_infected_usb}")
        
        # 每天保存结果
        save_daily_result(simulator, step)
    
    print("模拟完成！")
    return simulator

def save_daily_result(simulator, day):
    """保存每天的模拟结果"""
    result_data = []
    for idx in range(len(simulator.gdf)):
        node_data = {
            'building_id': simulator.G.nodes[idx]['building_id'],
            'geometry': simulator.G.nodes[idx]['geometry'],
            'entry_point': simulator.G.nodes[idx]['entry_point'],
            'population': simulator.G.nodes[idx]['population'],
            'infected_usb': simulator.G.nodes[idx]['infected_usb'],
            'total_usb': simulator.G.nodes[idx]['total_usb'],
            'infection_time': simulator.G.nodes[idx]['infection_time'],
            'source': simulator.G.nodes[idx]['source'],
            'day': day  # 添加日期字段
        }
        result_data.append(node_data)
    
    result_gdf = gpd.GeoDataFrame(result_data, crs=simulator.gdf.crs)
    
    # 确保entry_point作为普通列保存
    result_gdf['entry_point'] = result_gdf['entry_point'].astype(str)
    
    output_path = f'data/daily_results/day_{day}.geojson'
    result_gdf.to_file(output_path, driver='GeoJSON')
    print(f"Day {day} 状态已保存到: {output_path}")

if __name__ == "__main__":
    run_simulation()
