// 地图和图层变量
let map;
let markersLayer;
let heatmapLayer;
let gridLayer;
let currentDay = 0;
let maxDay = 100;
let totalBuildings = 0;
let totalUSB = 0;

// 初始化地图
function initMap() {
    // 创建没有底图的地图容器
    map = L.map('map', {
        center: [37.765, -122.41],
        zoom: 14,
        zoomControl: true,
        attributionControl: false,
        minZoom: 12,
        maxZoom: 18
    });
    
    // 添加缩放控件
    L.control.zoom({
        position: 'topright'
    }).addTo(map);
    
    // 添加网格层
    gridLayer = L.gridLayer({
        tileSize: 256,
        opacity: 0.2,
        zIndex: 1
    });
    gridLayer.addTo(map);
    
    // 初始化图层
    markersLayer = L.layerGroup().addTo(map);
    heatmapLayer = L.heatLayer([], { 
        radius: 20,
        blur: 25,
        minOpacity: 0.6,
        gradient: {
            0.1: 'rgba(0, 188, 212, 0.7)',
            0.3: 'rgba(76, 175, 80, 0.7)',
            0.5: 'rgba(255, 235, 59, 0.7)',
            0.7: 'rgba(255, 152, 0, 0.7)',
            0.9: 'rgba(244, 67, 54, 0.7)'
        }
    }).addTo(map);
    
    // 添加初始装饰元素
    addDecorativeElements();
    
    // 设置事件监听器
    setupEventListeners();
    
    // 加载第0天的数据
    setTimeout(() => {
        document.querySelector('.loading').style.display = 'none';
        loadDayData(0);
    }, 1500);
}

// 添加装饰元素（网格和参考点）
function addDecorativeElements() {
    // 添加参考点
    const bounds = map.getBounds();
    const north = bounds.getNorth();
    const south = bounds.getSouth();
    const east = bounds.getEast();
    const west = bounds.getWest();
    
    for (let i = 0; i < 50; i++) {
        const lat = south + Math.random() * (north - south);
        const lng = west + Math.random() * (east - west);
        L.circleMarker([lat, lng], {
            radius: 1,
            color: 'rgba(255, 255, 255, 0.15)',
            fillOpacity: 0.5
        }).addTo(map);
    }
    
    // 添加边界标记
    L.rectangle(bounds, {
        color: 'rgba(255, 255, 255, 0.3)',
        weight: 2,
        fill: false
    }).addTo(map);
    
    // 添加方向标记
    L.marker([north - 0.005, east - 0.005], {
        icon: L.divIcon({
            className: 'direction-icon',
            html: '<div style="font-size: 24px; color: rgba(52, 152, 219, 0.7);">N</div>',
            iconSize: [24, 24]
        })
    }).addTo(map);
}

// 设置事件监听器
function setupEventListeners() {
    // 时间滑块
    document.getElementById('day-slider').addEventListener('input', function(e) {
        currentDay = parseInt(e.target.value);
        updateDayDisplay();
        loadDayData(currentDay);
    });
    
    // 前一天按钮
    document.getElementById('prev-day').addEventListener('click', function() {
        if (currentDay > 0) {
            currentDay--;
            document.getElementById('day-slider').value = currentDay;
            updateDayDisplay();
            loadDayData(currentDay);
        }
    });
    
    // 后一天按钮
    document.getElementById('next-day').addEventListener('click', function() {
        if (currentDay < maxDay) {
            currentDay++;
            document.getElementById('day-slider').value = currentDay;
            updateDayDisplay();
            loadDayData(currentDay);
        }
    });
}

// 更新日期显示
function updateDayDisplay() {
    document.getElementById('day-display').textContent = `Day ${currentDay}`;
}

// 加载指定日期的数据
function loadDayData(day) {
    const url = `data/daily_results/day_${day}.geojson`;
    
    // 显示加载状态
    document.getElementById('infected-buildings').textContent = '...';
    document.getElementById('infected-usb').textContent = '...';
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            updateMapWithData(data, day);
        })
        .catch(error => {
            console.error(`加载第 ${day} 天数据时出错:`, error);
            // 回退到默认视图
            markersLayer.clearLayers();
            heatmapLayer.setLatLngs([]);
            document.getElementById('infected-buildings').textContent = '0';
            document.getElementById('infected-usb').textContent = '0';
        });
}

// 使用数据更新地图
function updateMapWithData(geojsonData, day) {
    // 清除之前的标记
    markersLayer.clearLayers();
    
    // 准备热力图数据
    const heatData = [];
    let infectedBuildings = 0;
    let infectedUSB = 0;
    
    // 如果是第一次加载，记录总数
    if (totalBuildings === 0) {
        totalBuildings = geojsonData.features.length;
        document.getElementById('total-buildings').textContent = totalBuildings.toLocaleString();
        
        // 计算总USB
        totalUSB = geojsonData.features.reduce((sum, feature) => {
            return sum + feature.properties.total_usb;
        }, 0);
        document.getElementById('total-usb').textContent = totalUSB.toLocaleString();
    }
    
    // 处理每个要素
    geojsonData.features.forEach(feature => {
        const props = feature.properties;
        
        // 获取几何坐标 - 处理多边形和点
        let coords;
        if (feature.geometry.type === "Polygon") {
            // 多边形：使用第一个坐标点
            coords = feature.geometry.coordinates[0][0];
        } else if (feature.geometry.type === "Point") {
            // 点：直接使用坐标
            coords = feature.geometry.coordinates;
        } else {
            console.warn("未知几何类型:", feature.geometry.type);
            return;
        }
        
        // 统计感染情况
        if (props.infected_usb > 0) {
            infectedBuildings++;
            infectedUSB += props.infected_usb;
            
            // 添加热力图点
            heatData.push([coords[1], coords[0], Math.min(100, props.infected_usb)]);
            
            // 创建标记
            const marker = L.circleMarker([coords[1], coords[0]], {
                radius: Math.min(20, 6 + props.infected_usb * 0.08),
                fillColor: getColorForInfection(props.infected_usb),
                color: '#fff',
                weight: 1,
                opacity: 0.9,
                fillOpacity: 0.7
            });
            
            // 添加弹出信息
            marker.bindPopup(`
                <div class="popup-content">
                    <h3>建筑物 ${props.building_id}</h3>
                    <div class="popup-stats">
                        <div class="popup-stat">
                            <span class="popup-label">感染 USB:</span>
                            <span class="popup-value infected">${props.infected_usb}</span>
                            <span class="popup-total">/${props.total_usb}</span>
                        </div>
                        <div class="popup-stat">
                            <span class="popup-label">人口:</span>
                            <span class="popup-value">${props.population}</span>
                        </div>
                        <div class="popup-stat">
                            <span class="popup-label">感染时间:</span>
                            <span class="popup-value">${props.infection_time >= 0 ? 'Day ' + props.infection_time : '未感染'}</span>
                        </div>
                        <div class="popup-stat">
                            <span class="popup-label">来源:</span>
                            <span class="popup-value">${props.source >= 0 ? '建筑物 ' + props.source : '初始点'}</span>
                        </div>
                    </div>
                </div>
            `);
            
            markersLayer.addLayer(marker);
        }
    });
    
    // 更新热力图
    heatmapLayer.setLatLngs(heatData);
    
    // 更新信息面板
    document.getElementById('infected-buildings').textContent = infectedBuildings.toLocaleString();
    document.getElementById('infected-usb').textContent = infectedUSB.toLocaleString();
    
    // 添加动态标题
    document.querySelector('h1').innerHTML = `USB传播模拟可视化 <span style="font-size: 0.8em; color: #2ecc71;">Day ${day}</span>`;
}

// 根据感染数量获取颜色
function getColorForInfection(infectedCount) {
    if (infectedCount <= 5) return '#00bcd4'; // 青色
    if (infectedCount <= 10) return '#4caf50'; // 绿色
    if (infectedCount <= 20) return '#ffeb3b'; // 黄色
    if (infectedCount <= 30) return '#ff9800'; // 橙色
    if (infectedCount <= 50) return '#ff5722'; // 深橙色
    return '#f44336'; // 红色
}

// 添加自定义CSS到页面
function addCustomCSS() {
    const style = document.createElement('style');
    style.textContent = `
        .popup-content {
            color: #333;
            min-width: 250px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .popup-content h3 {
            color: #3498db;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #3498db;
        }
        
        .popup-stats {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }
        
        .popup-stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .popup-label {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .popup-value {
            font-weight: bold;
            color: #3498db;
        }
        
        .popup-value.infected {
            color: #e74c3c;
            font-size: 1.2em;
        }
        
        .popup-total {
            color: #7f8c8d;
        }
        
        .direction-icon {
            text-align: center;
            font-weight: bold;
        }
    `;
    document.head.appendChild(style);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    addCustomCSS();
    initMap();
});