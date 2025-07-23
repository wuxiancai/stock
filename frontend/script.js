// API配置
const API_BASE_URL = 'http://localhost:8080/api/v1';

// 全局变量
let indicesData = [];
let refreshInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadIndices();
    // 设置自动刷新（每30秒）
    refreshInterval = setInterval(loadIndices, 30000);
});

// 加载指数数据
async function loadIndices() {
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const gridEl = document.getElementById('indices-grid');
    const lastUpdateEl = document.getElementById('last-update');

    try {
        // 显示加载状态
        loadingEl.style.display = 'block';
        errorEl.style.display = 'none';
        gridEl.style.display = 'none';
        lastUpdateEl.style.display = 'none';

        // 调用API获取指数数据
        const response = await fetch(`${API_BASE_URL}/market/indices`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            mode: 'cors'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        indicesData = data;

        // 隐藏加载状态
        loadingEl.style.display = 'none';

        // 渲染指数数据
        renderIndices(data);

        // 显示网格和更新时间
        gridEl.style.display = 'grid';
        lastUpdateEl.style.display = 'block';
        updateLastUpdateTime();
        
        console.log('✅ 从API获取数据成功');

    } catch (error) {
        console.warn('⚠️ API请求失败，使用模拟数据:', error.message);
        
        // API失败时使用模拟数据
        const mockResult = getMockData();
        indicesData = mockResult;
        
        // 隐藏加载状态
        loadingEl.style.display = 'none';
        
        // 渲染模拟数据
        renderIndices(mockResult.data);
        
        // 显示网格和更新时间
        gridEl.style.display = 'grid';
        lastUpdateEl.style.display = 'block';
        updateLastUpdateTime();
        
        // 显示提示信息
        const messageElement = document.createElement('div');
        messageElement.className = 'mock-data-notice';
        messageElement.innerHTML = `
            <p>📡 当前显示模拟数据</p>
            <p>💡 ${mockResult.message}</p>
            <p>🔧 请启动后端服务以获取真实数据</p>
        `;
        messageElement.style.cssText = `
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
            color: #856404;
            font-size: 14px;
        `;
        
        // 插入到网格前面
        gridEl.parentNode.insertBefore(messageElement, gridEl);
        
        // 5秒后移除提示
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 5000);
    }
}

// 获取模拟数据（当API不可用时使用）
function getMockData() {
    // 生成随机波动的数据
    const baseData = [
        { code: "000001", name: "上证指数", base: 3000, range: 100 },
        { code: "399001", name: "深证成指", base: 10000, range: 500 },
        { code: "399006", name: "创业板指", base: 2000, range: 100 },
        { code: "000300", name: "沪深300", base: 4000, range: 200 },
        { code: "000905", name: "中证500", base: 6000, range: 300 },
        { code: "000016", name: "上证50", base: 2500, range: 100 }
    ];

    const indices = baseData.map(item => {
        const change = (Math.random() - 0.5) * item.range * 0.2;
        const current_price = item.base + change;
        const change_percent = (change / item.base) * 100;
        
        return {
            code: item.code,
            name: item.name,
            current_price: Math.round(current_price * 100) / 100,
            change: Math.round(change * 100) / 100,
            change_percent: Math.round(change_percent * 100) / 100,
            volume: Math.floor(Math.random() * 400000000) + 100000000,
            turnover: Math.round((Math.random() * 200 + 100) * 100) / 100,
            high: Math.round((current_price + Math.random() * 50) * 100) / 100,
            low: Math.round((current_price - Math.random() * 50) * 100) / 100,
            open: Math.round((item.base + (Math.random() - 0.5) * 40) * 100) / 100,
            prev_close: item.base
        };
    });

    return {
        success: true,
        data: indices,
        timestamp: new Date().toISOString(),
        message: "模拟数据 - 每次刷新都会生成新的随机数据"
    };
}

// 渲染指数数据
function renderIndices(indices) {
    const gridEl = document.getElementById('indices-grid');
    gridEl.innerHTML = '';
    
    indices.forEach(index => {
        const card = document.createElement('div');
        card.className = 'index-card';
        
        // 确定涨跌状态
        const isPositive = index.change >= 0;
        const changeClass = isPositive ? 'positive' : 'negative';
        const changeSymbol = isPositive ? '+' : '';
        
        card.innerHTML = `
            <div class="index-header">
                <h3 class="index-name">${index.name}</h3>
                <span class="index-code">${index.code}</span>
            </div>
            <div class="index-price">
                <span class="current-price">${index.current_price.toFixed(2)}</span>
            </div>
            <div class="index-change ${changeClass}">
                <span class="change-amount">${changeSymbol}${index.change.toFixed(2)}</span>
                <span class="change-percent">(${changeSymbol}${index.change_percent.toFixed(2)}%)</span>
            </div>
            <div class="index-details">
                <div class="detail-row">
                    <span class="detail-label">开盘:</span>
                    <span class="detail-value">${index.open.toFixed(2)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">最高:</span>
                    <span class="detail-value">${index.high.toFixed(2)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">最低:</span>
                    <span class="detail-value">${index.low.toFixed(2)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">昨收:</span>
                    <span class="detail-value">${index.prev_close.toFixed(2)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">成交量:</span>
                    <span class="detail-value">${formatVolume(index.volume)}</span>
                </div>
                ${index.turnover ? `
                <div class="detail-row">
                    <span class="detail-label">换手率:</span>
                    <span class="detail-value">${index.turnover.toFixed(2)}%</span>
                </div>
                ` : ''}
            </div>
        `;
        
        gridEl.appendChild(card);
    });
}

// 创建指数卡片
function createIndexCard(index) {
    // 计算涨跌幅和趋势
    const change = parseFloat(index.change || 0);
    const changePercent = parseFloat(index.change_percent || 0);
    const price = parseFloat(index.current_price || index.close || 0);
    
    // 确定趋势方向
    let trendClass = 'trend-flat';
    let changeClass = 'change-flat';
    let trendIcon = 'fas fa-minus';
    
    if (change > 0) {
        trendClass = 'trend-up';
        changeClass = 'change-up';
        trendIcon = 'fas fa-arrow-up';
    } else if (change < 0) {
        trendClass = 'trend-down';
        changeClass = 'change-down';
        trendIcon = 'fas fa-arrow-down';
    }

    // 格式化数值
    const formatNumber = (num, decimals = 2) => {
        if (num === null || num === undefined || isNaN(num)) return '--';
        return Number(num).toFixed(decimals);
    };

    const formatPercent = (num) => {
        if (num === null || num === undefined || isNaN(num)) return '--';
        const formatted = Number(num).toFixed(2);
        return num > 0 ? `+${formatted}%` : `${formatted}%`;
    };

    return `
        <div class="index-card">
            <div class="index-header">
                <div>
                    <div class="index-name">${index.name || index.ts_code || '未知指数'}</div>
                    <div class="index-code">${index.ts_code || index.code || '--'}</div>
                </div>
                <div class="index-trend ${trendClass}">
                    <i class="${trendIcon}"></i>
                    ${change > 0 ? '上涨' : change < 0 ? '下跌' : '平盘'}
                </div>
            </div>
            
            <div class="index-price">${formatNumber(price)}</div>
            
            <div class="index-change">
                <span class="change-value ${changeClass}">
                    ${change > 0 ? '+' : ''}${formatNumber(change)}
                </span>
                <span class="change-percent ${changeClass}">
                    ${formatPercent(changePercent)}
                </span>
            </div>
            
            <div class="index-stats">
                <div class="stat-item">
                    <div class="stat-label">今开</div>
                    <div class="stat-value">${formatNumber(index.open)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">昨收</div>
                    <div class="stat-value">${formatNumber(index.pre_close)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">最高</div>
                    <div class="stat-value">${formatNumber(index.high)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">最低</div>
                    <div class="stat-value">${formatNumber(index.low)}</div>
                </div>
            </div>
        </div>
    `;
}

// 刷新数据
function refreshData() {
    const refreshBtn = document.querySelector('.refresh-btn');
    const icon = refreshBtn.querySelector('i');
    
    // 添加旋转动画
    icon.style.transform = 'rotate(360deg)';
    
    // 重新加载数据
    loadIndices();
    
    // 重置图标动画
    setTimeout(() => {
        icon.style.transform = 'rotate(0deg)';
    }, 500);
}

// 更新最后更新时间
function updateLastUpdateTime() {
    const updateTimeEl = document.getElementById('update-time');
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    updateTimeEl.textContent = timeString;
}

// 页面卸载时清理定时器
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

// 处理网络错误和重试逻辑
function handleNetworkError(error) {
    console.error('网络错误:', error);
    
    // 如果是网络错误，可以尝试重连
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        setTimeout(() => {
            console.log('尝试重新连接...');
            loadIndices();
        }, 5000);
    }
}

// 添加键盘快捷键支持
document.addEventListener('keydown', function(event) {
    // F5 或 Ctrl+R 刷新数据
    if (event.key === 'F5' || (event.ctrlKey && event.key === 'r')) {
        event.preventDefault();
        refreshData();
    }
});

// 添加页面可见性变化处理
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // 页面重新可见时刷新数据
        loadIndices();
    } else {
        // 页面隐藏时清除定时器
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
    
    if (document.visibilityState === 'visible' && !refreshInterval) {
        // 重新设置定时器
        refreshInterval = setInterval(loadIndices, 30000);
    }
});

// 添加错误边界处理
window.addEventListener('error', function(event) {
    console.error('全局错误:', event.error);
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('未处理的Promise拒绝:', event.reason);
    event.preventDefault();
});