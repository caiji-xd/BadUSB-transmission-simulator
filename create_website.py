# create_website.py
import os
import shutil

def create_simulation_website():
    """创建模拟结果网站"""
    # 创建网站目录
    website_dir = 'visualization/simulation_website'
    os.makedirs(website_dir, exist_ok=True)
    
    # 复制HTML和JS文件
    shutil.copy('visualization/simulation_viewer.html', os.path.join(website_dir, 'index.html'))
    shutil.copy('visualization/simulation_viewer.js', os.path.join(website_dir, 'simulation_viewer.js'))
    
    # 创建数据符号链接（或复制数据）
    data_dir = os.path.join(website_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 在实际部署中，应该复制数据而不是使用符号链接
    source_data = os.path.abspath('data/daily_results')
    target_data = os.path.join(data_dir, 'daily_results')
    
    if not os.path.exists(target_data):
        os.symlink(source_data, target_data)
        print(f"已创建数据符号链接: {target_data} -> {source_data}")
    
    print(f"网站已创建在: {website_dir}")
    print(f"请使用浏览器打开: {os.path.join(website_dir, 'index.html')}")

if __name__ == "__main__":
    create_simulation_website()