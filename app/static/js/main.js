// 主要JavaScript功能
class StockTradingSystem {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.init();
    }

    init() {
        this.updateDateTime();
        this.loadMarketData();
        this.loadCryptoData();
        this.loadStockData();
        this.bindEvents();
        
        // 每30秒更新一次数据
        setInterval(() => {
            this.updateDateTime();
            this.loadMarketData();
            this.loadCryptoData();
            this.loadStockData();
        }, 30000);
    }

    // 更新日期时间
    updateDateTime() {
        const now = new Date();
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZone: 'Asia/Shanghai'
        };
        const dateTimeStr = now.toLocaleDateString('zh-CN', options);
        document.getElementById('datetime').textContent = dateTimeStr;
    }

    // 绑定事件
    bindEvents() {
        // 筛选按钮事件
        const applyFilterBtn = document.querySelector('.filter-controls .btn-primary');
        const clearFilterBtn = document.querySelector('.filter-controls .btn-secondary');
        
        if (applyFilterBtn) {
            applyFilterBtn.addEventListener('click', () => this.applyFilters());
        }
        
        if (clearFilterBtn) {
            clearFilterBtn.addEventListener('click', () => this.clearFilters());
        }

        // 功能按钮事件
        this.bindActionButtons();
    }

    // 绑定功能按钮
    bindActionButtons() {
        const buttons = document.querySelectorAll('.action-buttons .btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const buttonText = e.target.textContent.trim();
                this.handleButtonClick(buttonText);
            });
        });
    }

    // 处理按钮点击
    handleButtonClick(buttonText) {
        switch(buttonText) {
            case '买入':
                this.showMessage('买入功能', 'success');
                break;
            case '卖出':
                this.showMessage('卖出功能', 'warning');
                break;
            case '立即刷新数据':
                this.refreshAllData();
                break;
            case '创业板':
                this.loadStockData('创业板');
                break;
            case '科创板':
                this.loadStockData('科创板');
                break;
            case '自选股':
                this.loadFavoriteStocks();
                break;
            default:
                this.showMessage(`${buttonText} 功能开发中...`, 'info');
        }
    }

    // 加载市场数据
    async loadMarketData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/market/indices`);
            if (response.ok) {
                const data = await response.json();
                this.updateMarketIndices(data);
            } else {
                // 使用模拟数据
                this.updateMarketIndices(this.getMockMarketData());
            }
        } catch (error) {
            console.log('使用模拟市场数据');
            this.updateMarketIndices(this.getMockMarketData());
        }
    }

    // 更新市场指数显示
    updateMarketIndices(data) {
        const indices = document.querySelectorAll('.index-card');
        data.forEach((index, i) => {
            if (indices[i]) {
                const priceEl = indices[i].querySelector('.price');
                const changeEl = indices[i].querySelector('.change');
                const volumeEl = indices[i].querySelector('.volume');
                
                if (priceEl) priceEl.textContent = index.price;
                if (changeEl) {
                    changeEl.textContent = `${index.change} (${index.changePercent})`;
                    changeEl.className = `change ${index.change.startsWith('+') ? 'positive' : 'negative'}`;
                }
                if (volumeEl) volumeEl.textContent = `成交额: ${index.volume}`;
            }
        });
    }

    // 加载加密货币数据
    async loadCryptoData() {
        try {
            // 这里可以接入真实的加密货币API
            const cryptoData = this.getMockCryptoData();
            this.updateCryptoDisplay(cryptoData);
        } catch (error) {
            console.log('使用模拟加密货币数据');
            this.updateCryptoDisplay(this.getMockCryptoData());
        }
    }

    // 更新加密货币显示
    updateCryptoDisplay(data) {
        const cryptoCards = document.querySelectorAll('.crypto-card');
        data.forEach((crypto, i) => {
            if (cryptoCards[i]) {
                const priceEl = cryptoCards[i].querySelector('.crypto-price');
                const changeEl = cryptoCards[i].querySelector('.crypto-change');
                
                if (priceEl) priceEl.textContent = crypto.price;
                if (changeEl) {
                    changeEl.textContent = `${crypto.change} (${crypto.changePercent})`;
                    changeEl.className = `crypto-change ${crypto.change.startsWith('+') ? 'positive' : 'negative'}`;
                }
            }
        });
    }

    // 加载股票数据
    async loadStockData(board = '创业板') {
        try {
            const response = await fetch(`${this.apiBaseUrl}/stocks/list?board=${encodeURIComponent(board)}`);
            if (response.ok) {
                const data = await response.json();
                this.updateStockTable(data);
            } else {
                // 使用模拟数据
                this.updateStockTable(this.getMockStockData());
            }
        } catch (error) {
            console.log('使用模拟股票数据');
            this.updateStockTable(this.getMockStockData());
        }
    }

    // 更新股票表格
    updateStockTable(stocks) {
        const tbody = document.querySelector('#stockTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        stocks.forEach(stock => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${stock.code}</td>
                <td>${stock.name}</td>
                <td>${stock.industry}</td>
                <td class="${stock.changePercent >= 0 ? 'positive' : 'negative'}">${stock.changePercent >= 0 ? '+' : ''}${stock.changePercent}%</td>
                <td>¥${stock.price}</td>
                <td>${stock.turnoverRate}</td>
                <td>${stock.volumeRatio}</td>
                <td>${stock.pe}</td>
                <td>${stock.amount}</td>
                <td>${stock.roe}</td>
                <td>${stock.netProfitGrowth}%</td>
            `;
            tbody.appendChild(row);
        });
    }

    // 应用筛选
    applyFilters() {
        const filters = this.getFilterValues();
        this.showMessage('正在应用筛选条件...', 'info');
        
        // 这里可以调用API进行筛选
        setTimeout(() => {
            this.loadStockData();
            this.showMessage('筛选完成', 'success');
        }, 1000);
    }

    // 清除筛选
    clearFilters() {
        const inputs = document.querySelectorAll('.filter-input');
        inputs.forEach(input => input.value = '');
        this.showMessage('筛选条件已清除', 'info');
        this.loadStockData();
    }

    // 获取筛选值
    getFilterValues() {
        const inputs = document.querySelectorAll('.filter-input');
        const filters = {};
        inputs.forEach((input, index) => {
            if (input.value) {
                filters[`filter_${index}`] = input.value;
            }
        });
        return filters;
    }

    // 刷新所有数据
    refreshAllData() {
        this.showMessage('正在刷新数据...', 'info');
        this.loadMarketData();
        this.loadCryptoData();
        this.loadStockData();
        this.showMessage('数据刷新完成', 'success');
    }

    // 加载自选股
    async loadFavoriteStocks() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/favorites`);
            if (response.ok) {
                const data = await response.json();
                this.updateStockTable(data);
                this.showMessage('自选股加载完成', 'success');
            } else {
                this.showMessage('请先登录', 'warning');
            }
        } catch (error) {
            this.showMessage('加载自选股失败', 'error');
        }
    }

    // 显示消息
    showMessage(message, type = 'info') {
        // 创建消息提示
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${type}`;
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        // 设置背景色
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#06b6d4'
        };
        messageEl.style.backgroundColor = colors[type] || colors.info;

        document.body.appendChild(messageEl);

        // 3秒后自动移除
        setTimeout(() => {
            messageEl.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.parentNode.removeChild(messageEl);
                }
            }, 300);
        }, 3000);
    }

    // 模拟数据
    getMockMarketData() {
        return [
            { price: '3503.78', change: '-1.22', changePercent: '-0.03%', volume: '5724.19亿' },
            { price: '11007.49', change: '+83.85', changePercent: '+0.89%', volume: '9696.74亿' },
            { price: '2296.88', change: '+19.73', changePercent: '+0.87%', volume: '4440.17亿' },
            { price: '1007.89', change: '+0.37', changePercent: '+0.04%', volume: '268.07亿' }
        ];
    }

    getMockCryptoData() {
        return [
            { price: '$119296.18', change: '+625.08', changePercent: '+0.53%' },
            { price: '$3803.94', change: '+30.12', changePercent: '+0.80%' },
            { price: '$191.26', change: '+8.84', changePercent: '+4.85%' },
            { price: '$3.57', change: '+0.08', changePercent: '+1.99%' },
            { price: '$762.90', change: '-11.88', changePercent: '-1.58%' },
            { price: '$0.275110', change: '+0.020950', changePercent: '+8.24%' }
        ];
    }

    getMockStockData() {
        return [
            {
                code: '300004.SZ',
                name: '南风股份',
                industry: '专用设备',
                changePercent: 3.55,
                price: '23.58',
                turnoverRate: '1.20',
                volumeRatio: '0.89',
                pe: '27.91',
                amount: '2.04',
                roe: '245.01',
                netProfitGrowth: '1364.30'
            },
            {
                code: '300015.SZ',
                name: '爱尔眼科',
                industry: '医疗服务',
                changePercent: -2.15,
                price: '18.45',
                turnoverRate: '0.85',
                volumeRatio: '1.12',
                pe: '32.45',
                amount: '5.67',
                roe: '156.78',
                netProfitGrowth: '245.60'
            },
            {
                code: '300059.SZ',
                name: '东方财富',
                industry: '互联网金融',
                changePercent: 1.89,
                price: '15.67',
                turnoverRate: '2.34',
                volumeRatio: '1.45',
                pe: '28.90',
                amount: '12.34',
                roe: '189.45',
                netProfitGrowth: '567.89'
            }
        ];
    }
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new StockTradingSystem();
});