// 全局变量
let stockData = [];
let filteredData = [];
let indexData = [];
let currentSort = { field: 'pct_chg', order: 'desc' };

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    loadSystemStatus();
    loadStockData();
    setupEventListeners();
    
    // 延迟加载指数数据，确保DOM元素已存在
    setTimeout(loadIndexData, 100);
    
    // 每30秒刷新一次状态
    setInterval(loadSystemStatus, 30000);
}

// 设置事件监听器
function setupEventListeners() {
    // 搜索框实时搜索
    document.getElementById('searchStock').addEventListener('input', function() {
        applyFilter();
    });
    
    // 排序选择变化
    document.getElementById('sortBy').addEventListener('change', function() {
        currentSort.field = this.value;
        applyFilter();
    });
    
    document.getElementById('sortOrder').addEventListener('change', function() {
        currentSort.order = this.value;
        applyFilter();
    });
    
    // 九转序列筛选变化
    document.getElementById('tdSequentialFilter').addEventListener('change', function() {
        applyFilter();
    });
    
    // 表头点击排序
    setupTableHeaderSorting();
}

// 设置表头排序功能
function setupTableHeaderSorting() {
    document.addEventListener('click', function(e) {
        if (e.target.closest('.sortable')) {
            const th = e.target.closest('.sortable');
            const field = th.getAttribute('data-field');
            
            // 如果点击的是同一列，切换排序顺序
            if (currentSort.field === field) {
                currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
            } else {
                // 如果点击的是不同列，设置为降序
                currentSort.field = field;
                currentSort.order = 'desc';
            }
            
            // 更新下拉菜单的值
            document.getElementById('sortBy').value = field;
            document.getElementById('sortOrder').value = currentSort.order;
            
            // 更新表头排序图标
            updateSortIcons();
            
            // 应用排序
            applyFilter();
        }
    });
}

// 更新排序图标
function updateSortIcons() {
    // 清除所有排序图标
    document.querySelectorAll('.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // 为当前排序列添加对应图标
    const currentTh = document.querySelector(`[data-field="${currentSort.field}"]`);
    if (currentTh) {
        currentTh.classList.add(currentSort.order === 'asc' ? 'sort-asc' : 'sort-desc');
    }
}

// 加载系统状态
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // 显示日线数据统计
        document.getElementById('stockCount').textContent = formatNumber(data.daily_data.stock_count);
        document.getElementById('totalRecords').textContent = formatNumber(data.daily_data.total_records);
        document.getElementById('latestDate').textContent = formatDate(data.daily_data.latest_date);
        
        // 在控制台显示基础信息统计（可选）
        if (data.basic_data.total_records > 0) {
            console.log(`基础信息: ${data.basic_data.stock_count}只股票, ${data.basic_data.total_records}条记录, 最新日期: ${data.basic_data.latest_date}`);
        }
        
        // 在控制台显示融资融券数据统计
        if (data.margin_data && data.margin_data.total_records > 0) {
            console.log(`融资融券: ${data.margin_data.exchange_count}个交易所, ${data.margin_data.total_records}条记录, 最新日期: ${data.margin_data.latest_date}`);
        }
        
        // 在控制台显示个股资金流向数据统计
        if (data.moneyflow_data && data.moneyflow_data.total_records > 0) {
            console.log(`资金流向: ${data.moneyflow_data.stock_count}只股票, ${data.moneyflow_data.total_records}条记录, 最新日期: ${data.moneyflow_data.latest_date}`);
        }
        
        // 在控制台显示龙虎榜每日明细数据统计
        if (data.top_list_data && data.top_list_data.total_records > 0) {
            console.log(`龙虎榜每日明细: ${data.top_list_data.stock_count}只股票, ${data.top_list_data.total_records}条记录, 最新日期: ${data.top_list_data.latest_date}`);
        }
        
        // 在控制台显示龙虎榜机构明细数据统计
        if (data.top_inst_data && data.top_inst_data.total_records > 0) {
            console.log(`龙虎榜机构明细: ${data.top_inst_data.stock_count}只股票, ${data.top_inst_data.total_records}条记录, 最新日期: ${data.top_inst_data.latest_date}`);
        }
        
        // 更新状态指示器
        const statusElement = document.getElementById('systemStatus');
        statusElement.innerHTML = '<span class="status-indicator status-online"></span>运行中';
        
    } catch (error) {
        console.error('加载系统状态失败:', error);
        const statusElement = document.getElementById('systemStatus');
        statusElement.innerHTML = '<span class="status-indicator status-offline"></span>离线';
    }
}

// 加载股票数据
async function loadStockData() {
    try {
        showLoading();
        const response = await fetch('/api/stocks');
        const data = await response.json();
        
        if (data.stocks) {
            stockData = data.stocks;
            filteredData = [...stockData];
            applyFilter();
            showToast('数据加载成功', 'success');
        } else {
            showToast(data.message || '暂无数据', 'warning');
        }
        
    } catch (error) {
        console.error('加载股票数据失败:', error);
        showToast('加载数据失败', 'error');
        hideLoading();
    }
}

// 应用筛选和排序
function applyFilter() {
    const searchTerm = document.getElementById('searchStock').value.toLowerCase();
    const sortField = document.getElementById('sortBy').value;
    const sortOrder = document.getElementById('sortOrder').value;
    const tdSequentialFilter = document.getElementById('tdSequentialFilter').value;
    
    // 筛选数据
    filteredData = stockData.filter(stock => {
        // 股票代码筛选
        if (searchTerm && !stock.ts_code.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        // 九转序列筛选
        if (tdSequentialFilter) {
            const tdValue = parseFloat(stock.td_sequential) || 0;
            switch (tdSequentialFilter) {
                case 'red':
                    if (tdValue <= 2) return false; // 红色信号：大于2
                    break;
                case 'green':
                    if (tdValue >= -2) return false; // 绿色信号：小于-2
                    break;
                case 'high':
                    if (tdValue <= 7) return false; // 高位：大于7
                    break;
                case 'low':
                    if (tdValue >= -7) return false; // 低位：小于-7
                    break;
            }
        }
        
        return true;
    });
    
    // 排序数据
    filteredData.sort((a, b) => {
        let aVal = a[sortField];
        let bVal = b[sortField];
        
        // 处理数值类型字段
        if (['open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount', 'td_sequential'].includes(sortField)) {
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
            
            if (sortOrder === 'desc') {
                return bVal - aVal;
            } else {
                return aVal - bVal;
            }
        } else {
            // 处理字符串类型字段（股票代码、名称等）
            aVal = String(aVal || '').toLowerCase();
            bVal = String(bVal || '').toLowerCase();
            
            if (sortOrder === 'desc') {
                return bVal.localeCompare(aVal);
            } else {
                return aVal.localeCompare(bVal);
            }
        }
    });
    
    renderStockTable();
}

// 渲染股票表格
function renderStockTable() {
    const tbody = document.getElementById('stockTableBody');
    const dataCount = document.getElementById('dataCount');
    
    if (filteredData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="21" class="text-center text-muted">
                    <i class="fas fa-inbox fa-2x mb-2"></i><br>
                    暂无数据
                </td>
            </tr>
        `;
        dataCount.textContent = '0';
        return;
    }
    
    const rows = filteredData.map(stock => {
        const pctChgClass = getPctChgClass(stock.pct_chg);
        const changeClass = getPctChgClass(stock.change);
        
        return `
            <tr class="fade-in">
                <td class="stock-code">${stock.ts_code}</td>
                <td class="stock-name"><a href="/stock/${stock.ts_code}" target="_blank" style="text-decoration: none; color: #007bff;">${stock.name || stock.ts_code}</a></td>
                <td class="text-truncate" style="max-width: 80px;" title="${stock.industry || '-'}">${stock.industry || '-'}</td>
                <td class="text-truncate" style="max-width: 60px;" title="${stock.area || '-'}">${stock.area || '-'}</td>
                <td style="display: none;">${formatDate(stock.trade_date)}</td>
                <td class="number">${formatPrice(stock.open)}</td>
                <td class="number" style="display: none;">${formatPrice(stock.high)}</td>
                <td class="number" style="display: none;">${formatPrice(stock.low)}</td>
                <td class="number">${formatPrice(stock.close)}</td>
                <td class="number">${formatPrice(stock.pre_close)}</td>
                <td class="number ${changeClass}" style="display: none;">${formatChange(stock.change)}</td>
                <td class="number ${pctChgClass}">${formatPercent(stock.pct_chg)}</td>
                <td class="number">${stock.turnover_rate ? stock.turnover_rate.toFixed(2) + '%' : '-'}</td>
                <td class="number">${stock.volume_ratio ? stock.volume_ratio.toFixed(2) : '-'}</td>
                <td class="number">${stock.pe ? stock.pe.toFixed(2) : '-'}</td>
                <td class="number">${stock.pb ? stock.pb.toFixed(2) : '-'}</td>
                <td class="number">${stock.total_mv ? (stock.total_mv / 10000).toFixed(2) + '亿' : '-'}</td>
                <td class="number ${stock.net_mf_amount > 0 ? 'text-danger' : stock.net_mf_amount < 0 ? 'text-success' : ''}">${stock.net_mf_amount ? (Math.abs(stock.net_mf_amount) >= 10000 ? (stock.net_mf_amount / 10000).toFixed(2) + '亿' : stock.net_mf_amount.toFixed(0) + '万') : '-'}</td>
                <td class="number">${formatAmount(stock.amount)}</td>
                <td class="number">${formatTdSequential(stock.td_sequential)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-success" onclick="addToFavorites('${stock.ts_code}', '${stock.name || stock.ts_code}')" title="加入自选股">
                        <i class="fas fa-star"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = rows;
    dataCount.textContent = filteredData.length;
    
    // 更新排序图标
    updateSortIcons();
}

// 显示股票详情
async function showStockDetail(tsCode) {
    const modal = new bootstrap.Modal(document.getElementById('stockDetailModal'));
    const title = document.getElementById('stockDetailTitle');
    const content = document.getElementById('stockDetailContent');
    
    title.textContent = `股票详情 - ${tsCode}`;
    content.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
        </div>
    `;
    
    modal.show();
    
    try {
        const response = await fetch(`/api/stock/${tsCode}?days=30`);
        const data = await response.json();
        
        if (data.history && data.history.length > 0) {
            renderStockHistory(data.history);
        } else {
            content.innerHTML = '<p class="text-center text-muted">暂无历史数据</p>';
        }
        
    } catch (error) {
        console.error('加载股票详情失败:', error);
        content.innerHTML = '<p class="text-center text-danger">加载失败</p>';
    }
}

// 渲染股票历史数据
function renderStockHistory(history) {
    const content = document.getElementById('stockDetailContent');
    
    const tableHtml = `
        <div class="table-responsive">
            <table class="table table-sm table-striped">
                <thead>
                    <tr>
                        <th>交易日期</th>
                        <th>开盘价</th>
                        <th>最高价</th>
                        <th>最低价</th>
                        <th>收盘价</th>
                        <th>涨跌幅(%)</th>
                        <th>成交量</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.map(row => {
                        const pctChgClass = getPctChgClass(row.pct_chg);
                        return `
                            <tr>
                                <td>${formatDate(row.trade_date)}</td>
                                <td class="number">${formatPrice(row.open)}</td>
                                <td class="number">${formatPrice(row.high)}</td>
                                <td class="number">${formatPrice(row.low)}</td>
                                <td class="number">${formatPrice(row.close)}</td>
                                <td class="number ${pctChgClass}">${formatPercent(row.pct_chg)}</td>
                                <td class="number">${formatVolume(row.vol)}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    content.innerHTML = tableHtml;
}

// 手动同步数据
async function manualSync() {
    const button = event.target.closest('button');
    const originalHtml = button.innerHTML;
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 同步中...';
    
    try {
        const response = await fetch('/api/sync');
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            // 同步完成后重新加载数据
            setTimeout(() => {
                loadStockData();
                loadSystemStatus();
            }, 1000);
        } else {
            showToast(data.message, 'error');
        }
        
    } catch (error) {
        console.error('手动同步失败:', error);
        showToast('同步失败', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

// 同步股票基础信息
async function syncBasicData() {
    const button = event.target.closest('button');
    const originalHtml = button.innerHTML;
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 同步中...';
    
    try {
        const response = await fetch('/api/sync_basic');
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            // 同步完成后重新加载状态
            setTimeout(() => {
                loadSystemStatus();
            }, 1000);
        } else {
            showToast(data.message, 'error');
        }
        
    } catch (error) {
        console.error('基础信息同步失败:', error);
        showToast('基础信息同步失败', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

// 同步个股资金流向数据
async function syncMoneyflowData() {
    const button = event.target.closest('button');
    const originalHtml = button.innerHTML;
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 同步中...';
    
    try {
        const response = await fetch('/api/sync_moneyflow');
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            // 同步完成后重新加载状态
            setTimeout(() => {
                loadSystemStatus();
            }, 1000);
        } else {
            showToast(data.message, 'error');
        }
        
    } catch (error) {
        console.error('个股资金流向数据同步失败:', error);
        showToast('个股资金流向数据同步失败', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}



// 一键同步所有A股数据
// 显示日期选择弹窗
function showDateRangeModal() {
    // 创建模态框HTML
    const modalHtml = `
        <div class="modal fade" id="dateRangeModal" tabindex="-1" aria-labelledby="dateRangeModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="dateRangeModalLabel">选择同步日期范围</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <label for="startDate" class="form-label">开始日期</label>
                                <input type="date" class="form-control" id="startDate" required>
                            </div>
                            <div class="col-md-6">
                                <label for="endDate" class="form-label">结束日期</label>
                                <input type="date" class="form-control" id="endDate" required>
                            </div>
                        </div>
                        <div class="mt-3">
                            <small class="text-muted">
                                <i class="fas fa-info-circle"></i>
                                请选择需要同步的日期范围。如果不选择日期，将同步所有可用数据。
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="confirmDateRangeSync()">开始同步</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除已存在的模态框
    const existingModal = document.getElementById('dateRangeModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加模态框到页面
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 设置默认日期（开始日期为当前日期）
    const endDate = new Date();
    const startDate = new Date();
    
    document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('dateRangeModal'));
    modal.show();
}

// 确认日期范围并开始同步
function confirmDateRangeSync() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    // 验证日期
    if (!startDate || !endDate) {
        showToast('请选择开始日期和结束日期', 'error');
        return;
    }
    
    if (new Date(startDate) > new Date(endDate)) {
        showToast('开始日期不能晚于结束日期', 'error');
        return;
    }
    
    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('dateRangeModal'));
    modal.hide();
    
    // 开始同步
    syncAllAStockDataWithDateRange(startDate, endDate);
}

// 原有的同步函数，现在作为无日期范围的同步
function syncAllAStockData() {
    showDateRangeModal();
}

// 带日期范围的同步函数
async function syncAllAStockDataWithDateRange(startDate = null, endDate = null) {
    const button = document.querySelector('button[onclick="syncAllAStockData()"]');
    const originalHtml = button.innerHTML;
    
    // 创建进度显示区域
    const progressContainer = createProgressContainer();
    button.parentNode.insertBefore(progressContainer, button.nextSibling);
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 启动同步...';
    
    try {
        // 准备请求数据
        const requestData = {};
        if (startDate && endDate) {
            requestData.start_date = startDate;
            requestData.end_date = endDate;
        }
        
        // 启动同步任务
        const response = await fetch('/api/sync_all_a_stock_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        const data = await response.json();
        
        if (data.success) {
            // 启动SSE连接监听进度
            startSyncProgressMonitoring(button, originalHtml, progressContainer);
        } else {
            showToast('启动同步失败：' + data.message, 'error');
            button.disabled = false;
            button.innerHTML = originalHtml;
            progressContainer.remove();
        }
        
    } catch (error) {
        console.error('启动A股数据同步失败:', error);
        showToast('启动A股数据同步失败：' + error.message, 'error');
        button.disabled = false;
        button.innerHTML = originalHtml;
        progressContainer.remove();
    }
}

function createProgressContainer() {
    const container = document.createElement('div');
    container.className = 'sync-progress-container mt-2';
    container.innerHTML = `
        <div class="progress mb-2" style="height: 20px;">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 0%" 
                 aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
                0%
            </div>
        </div>
        <div class="sync-status">
            <small class="text-muted">
                <div class="current-step">准备开始...</div>
                <div class="estimated-time"></div>
                <div class="sync-details"></div>
            </small>
        </div>
    `;
    return container;
}

function startSyncProgressMonitoring(button, originalHtml, progressContainer) {
    const eventSource = new EventSource('/api/sync_progress');
    
    eventSource.onmessage = function(event) {
        const progress = JSON.parse(event.data);
        updateProgressDisplay(progress, progressContainer);
        
        if (!progress.is_syncing) {
            // 同步完成
            eventSource.close();
            
            if (progress.success) {
                // 显示详细的同步结果弹窗
                showSyncResultModal(progress);
                // 同步完成后重新加载数据
                setTimeout(() => {
                    loadStockData();
                    loadSystemStatus();
                }, 1000);
            } else {
                showToast('同步失败：' + progress.message, 'error');
            }
            
            // 恢复按钮状态
            button.disabled = false;
            button.innerHTML = originalHtml;
            
            // 延迟移除进度条
            setTimeout(() => {
                progressContainer.remove();
            }, 3000);
        }
    };
    
    eventSource.onerror = function(event) {
        console.error('SSE连接错误:', event);
        eventSource.close();
        button.disabled = false;
        button.innerHTML = originalHtml;
        progressContainer.remove();
        showToast('进度监控连接失败', 'error');
    };
}

function updateProgressDisplay(progress, container) {
    const progressBar = container.querySelector('.progress-bar');
    const currentStepEl = container.querySelector('.current-step');
    const estimatedTimeEl = container.querySelector('.estimated-time');
    const detailsEl = container.querySelector('.sync-details');
    
    // 更新进度条，确保百分比不超过100%
    const rawPercentage = (progress.progress / progress.total_steps) * 100;
    const percentage = Math.min(100, Math.max(0, Math.round(rawPercentage)));
    progressBar.style.width = percentage + '%';
    progressBar.textContent = percentage + '%';
    progressBar.setAttribute('aria-valuenow', percentage);
    
    // 更新当前步骤
    currentStepEl.textContent = progress.current_step || '准备中...';
    
    // 更新预计剩余时间
    if (progress.estimated_remaining > 0) {
        const minutes = Math.floor(progress.estimated_remaining / 60);
        const seconds = Math.round(progress.estimated_remaining % 60);
        estimatedTimeEl.textContent = `预计剩余: ${minutes}分${seconds}秒`;
    } else {
        estimatedTimeEl.textContent = '';
    }
    
    // 更新详细信息
    if (progress.details && progress.details.length > 0) {
        const latestDetail = progress.details[progress.details.length - 1];
        detailsEl.textContent = latestDetail;
    }
}



// 同步指数日线行情数据
async function syncIndexDaily() {
    try {
        showLoading();
        const response = await fetch('/api/sync_index_daily', {
            method: 'POST'
        });
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            showToast(data.message, 'success');
            // 刷新系统状态
            loadSystemStatus();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('同步指数日线数据失败:', error);
        showToast('同步指数日线数据失败', 'error');
    }
}

// 生成统一分析表数据
async function generateAnalysisData() {
    const button = event.target.closest('button');
    const originalHtml = button.innerHTML;
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';
    
    try {
        const response = await fetch('/api/generate_analysis_data', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            // 刷新系统状态
            setTimeout(() => {
                loadSystemStatus();
            }, 1000);
        } else {
            showToast(data.message, 'error');
        }
        
    } catch (error) {
        console.error('生成统一分析表失败:', error);
        showToast('生成统一分析表失败', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}





// 刷新数据
function refreshData() {
    loadStockData();
    loadSystemStatus();
}

// 显示加载状态
function showLoading() {
    const tbody = document.getElementById('stockTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="12" class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
            </td>
        </tr>
    `;
}

// 隐藏加载状态
function hideLoading() {
    // 由renderStockTable处理
}

// 显示Toast通知
function showToast(message, type = 'info') {
    const toast = document.getElementById('notificationToast');
    const toastMessage = document.getElementById('toastMessage');
    
    // 设置消息内容
    toastMessage.textContent = message;
    
    // 设置样式
    toast.className = 'toast';
    if (type === 'success') {
        toast.classList.add('bg-success', 'text-white');
    } else if (type === 'error') {
        toast.classList.add('bg-danger', 'text-white');
    } else if (type === 'warning') {
        toast.classList.add('bg-warning', 'text-dark');
    } else {
        toast.classList.add('bg-info', 'text-white');
    }
    
    // 显示Toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// 工具函数
function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString();
}

function formatPrice(price) {
    if (price === null || price === undefined) return '-';
    return parseFloat(price).toFixed(2);
}

function formatPercent(pct) {
    if (pct === null || pct === undefined) return '-';
    const value = parseFloat(pct);
    return (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
}

function formatChange(change) {
    if (change === null || change === undefined) return '-';
    const value = parseFloat(change);
    return (value >= 0 ? '+' : '') + value.toFixed(2);
}

function formatVolume(vol) {
    if (vol === null || vol === undefined) return '-';
    const value = parseFloat(vol);
    if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万';
    }
    return value.toFixed(0);
}

function formatAmount(amount) {
    if (amount === null || amount === undefined) return '-';
    const value = parseFloat(amount);
    if (value >= 100000) {
        return (value / 100000).toFixed(2) + '亿';
    } else if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万';
    }
    return value.toFixed(0);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${year}-${month}-${day}`;
}

function getPctChgClass(pctChg) {
    if (pctChg === null || pctChg === undefined) return '';
    const value = parseFloat(pctChg);
    if (value > 0) return 'text-rise';
    if (value < 0) return 'text-fall';
    return 'text-flat';
}

function formatTdSequential(tdSequential) {
    if (tdSequential === null || tdSequential === undefined) {
        return '-';
    }
    
    if (tdSequential > 0) {
        // 买入序列用红色
        return `<span style="color: #dc3545; font-weight: bold;">${tdSequential}</span>`;
    } else if (tdSequential < 0) {
        // 卖出序列用绿色
        return `<span style="color: #198754; font-weight: bold;">${Math.abs(tdSequential)}</span>`;
    }
    
    return '-';
}

// 加载指数数据
async function loadIndexData() {
    try {
        const response = await fetch('/api/index_daily?limit=50');
        const data = await response.json();
        
        indexData = data.index_daily || [];
        renderIndexTable();
        
        // 更新数据计数
        const countElement = document.getElementById('indexDataCount');
        if (countElement) {
            countElement.textContent = indexData.length;
        }
        
    } catch (error) {
        console.error('加载指数数据失败:', error);
        showToast('加载指数数据失败', 'error');
    }
}

// 刷新指数数据
function refreshIndexData() {
    loadIndexData();
}

// 渲染指数数据卡片
function renderIndexTable() {
    // 预定义的指数代码和名称映射
    const indexMapping = {
        '000001.SH': { name: '上证指数', id: 'index1' },
        '399001.SZ': { name: '深证成指', id: 'index2' },
        '399006.SZ': { name: '创业板指', id: 'index3' },
        '000688.SH': { name: '科创50', id: 'index4' },
        '000905.SH': { name: '中证500', id: 'index5' },
        '000300.SH': { name: '沪深300', id: 'index6' }
    };
    
    // 为每个卡片更新数据
    Object.keys(indexMapping).forEach(code => {
        const mapping = indexMapping[code];
        const indexInfo = indexData.find(item => item.ts_code === code);
        
        // 更新名称
        const nameElement = document.getElementById(mapping.id + 'Name');
        if (nameElement) {
            nameElement.textContent = mapping.name;
        }
        
        if (indexInfo) {
            // 更新收盘价
            const closeElement = document.getElementById(mapping.id + 'Close');
            if (closeElement) {
                closeElement.textContent = formatPrice(indexInfo.close);
                closeElement.className = 'fw-bold ' + getPctChgClass(indexInfo.pct_chg);
            }
            
            // 更新涨跌幅
            const pctChgElement = document.getElementById(mapping.id + 'PctChg');
            if (pctChgElement) {
                pctChgElement.textContent = formatPercent(indexInfo.pct_chg);
                pctChgElement.className = 'fw-bold ' + getPctChgClass(indexInfo.pct_chg);
            }
            
            // 更新成交额
            const amountElement = document.getElementById(mapping.id + 'Amount');
            if (amountElement) {
                amountElement.textContent = formatAmount(indexInfo.amount);
            }
        } else {
            // 如果没有数据，显示默认值
            const closeElement = document.getElementById(mapping.id + 'Close');
            const pctChgElement = document.getElementById(mapping.id + 'PctChg');
            const amountElement = document.getElementById(mapping.id + 'Amount');
            
            if (closeElement) closeElement.textContent = '-';
            if (pctChgElement) pctChgElement.textContent = '-';
            if (amountElement) amountElement.textContent = '-';
        }
    });
}

// 显示同步结果弹窗
function showSyncResultModal(progress) {
    const integrityReport = progress.integrity_report || {};
    const isComplete = integrityReport.is_complete !== false;
    const completionRate = integrityReport.completion_rate || 0;
    
    // 创建弹窗HTML
    const modalHtml = `
        <div class="modal fade" id="syncResultModal" tabindex="-1" aria-labelledby="syncResultModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header ${isComplete ? 'bg-success text-white' : 'bg-warning text-dark'}">
                        <h5 class="modal-title" id="syncResultModalLabel">
                            <i class="fas ${isComplete ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
                            ${isComplete ? '同步完成' : '同步完成（存在问题）'}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <div class="card border-primary">
                                    <div class="card-body text-center">
                                        <h6 class="card-title text-primary">同步数据量</h6>
                                        <h4 class="text-primary">${progress.total_count || 0}</h4>
                                        <small class="text-muted">条记录</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card border-${isComplete ? 'success' : 'warning'}">
                                    <div class="card-body text-center">
                                        <h6 class="card-title text-${isComplete ? 'success' : 'warning'}">完整性检查</h6>
                                        <h4 class="text-${isComplete ? 'success' : 'warning'}">${completionRate.toFixed(1)}%</h4>
                                        <small class="text-muted">${isComplete ? '数据完整' : '存在缺失'}</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${generateSyncDetailsHtml(progress, integrityReport)}
                        
                        ${generateIntegrityDetailsHtml(integrityReport)}
                    </div>
                    <div class="modal-footer">
                         <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                         ${!isComplete ? '<button type="button" class="btn btn-warning" onclick="retryIncompleteSync()">重新同步缺失数据</button>' : ''}
                         ${generateRecentDataSyncButton(integrityReport)}
                     </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除已存在的弹窗
    const existingModal = document.getElementById('syncResultModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新弹窗到页面
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 显示弹窗
    const modal = new bootstrap.Modal(document.getElementById('syncResultModal'));
    modal.show();
    
    // 弹窗关闭后移除DOM元素
    document.getElementById('syncResultModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// 生成同步详情HTML
function generateSyncDetailsHtml(progress, integrityReport) {
    if (!progress.results || progress.results.length === 0) {
        return '<div class="alert alert-info">无详细同步信息</div>';
    }
    
    let html = '<div class="mb-3"><h6>同步详情</h6><div class="table-responsive"><table class="table table-sm table-striped">';
    html += '<thead><tr><th>日期</th><th>同步数量</th><th>完整性状态</th></tr></thead><tbody>';
    
    progress.results.forEach(result => {
        const parts = result.split(': ');
        if (parts.length === 2) {
            const date = parts[0];
            const count = parts[1];
            const dateReport = integrityReport.details && integrityReport.details[date];
            const isDateComplete = dateReport ? dateReport.actual > 0 : true;
            
            html += `<tr>
                <td>${date}</td>
                <td>${count}</td>
                <td><span class="badge bg-${isDateComplete ? 'success' : 'warning'}">${isDateComplete ? '完整' : '不完整'}</span></td>
            </tr>`;
        }
    });
    
    html += '</tbody></table></div></div>';
    return html;
}

// 生成完整性检查详情HTML
function generateIntegrityDetailsHtml(integrityReport) {
    if (!integrityReport || integrityReport.error) {
        return `<div class="alert alert-warning">完整性检查失败: ${integrityReport.error || '未知错误'}</div>`;
    }
    
    let html = '<div class="mb-3"><h6>数据完整性分析</h6>';
    
    // 缺失日期
    if (integrityReport.missing_dates && integrityReport.missing_dates.length > 0) {
        html += '<div class="alert alert-danger">';
        html += '<strong>缺失数据的日期:</strong><br>';
        html += integrityReport.missing_dates.join(', ');
        html += '</div>';
    }
    
    // 不完整数据
    if (integrityReport.incomplete_data && integrityReport.incomplete_data.length > 0) {
        html += '<div class="alert alert-warning">';
        html += '<strong>数据不完整的日期:</strong><br>';
        integrityReport.incomplete_data.forEach(item => {
            html += `${item.date}: 完成率 ${item.completion_rate}% (${item.actual}/${item.expected})<br>`;
        });
        html += '</div>';
    }
    
    // 如果数据完整
    if (integrityReport.is_complete) {
        html += '<div class="alert alert-success">';
        html += '<i class="fas fa-check-circle"></i> 所有数据同步完整，无缺失或异常！';
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// 生成最近交易日同步按钮
function generateRecentDataSyncButton(integrityReport) {
    if (!integrityReport || !integrityReport.incomplete_data) {
        return '';
    }
    
    // 检查是否有最近20个交易日的不完整数据
    const recentIncompleteData = integrityReport.incomplete_data.filter(item => {
        const itemDate = new Date(item.date.replace(/-(\d{2})-(\d{2})$/, '-$2-$1'));
        const twentyDaysAgo = new Date();
        twentyDaysAgo.setDate(twentyDaysAgo.getDate() - 20);
        return itemDate >= twentyDaysAgo;
    });
    
    if (recentIncompleteData.length > 0) {
        const dateList = recentIncompleteData.map(item => item.date).join(',');
        return `<button type="button" class="btn btn-danger" onclick="syncRecentIncompleteData('${dateList}')">同步最近${recentIncompleteData.length}个交易日缺失数据</button>`;
    }
    
    return '';
}

// 同步最近不完整的数据
function syncRecentIncompleteData(dateList) {
    // 关闭当前弹窗
    const modal = bootstrap.Modal.getInstance(document.getElementById('syncResultModal'));
    if (modal) {
        modal.hide();
    }
    
    const dates = dateList.split(',');
    if (dates.length === 0) {
        showToast('没有需要同步的日期', 'warning');
        return;
    }
    
    const startDate = dates[dates.length - 1]; // 最早的日期
    const endDate = dates[0]; // 最晚的日期
    
    showToast(`正在同步最近${dates.length}个交易日的缺失数据...`, 'info');
    syncAllAStockDataWithDateRange(startDate, endDate);
}

// 重新同步缺失数据
function retryIncompleteSync() {
    // 关闭当前弹窗
    const modal = bootstrap.Modal.getInstance(document.getElementById('syncResultModal'));
    if (modal) {
        modal.hide();
    }
    
    // 触发重新同步
    showToast('正在重新同步缺失数据...', 'info');
    syncAllAStockData();
}

// 打开九转序列法筛选器

// 加入自选股功能
async function addToFavorites(tsCode, stockName) {
    try {
        const response = await fetch('/api/favorites/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ts_code: tsCode,
                name: stockName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`${stockName} 已加入自选股`, 'success');
        } else {
            showToast(data.message || '加入自选股失败', 'error');
        }
    } catch (error) {
        console.error('Error adding to favorites:', error);
        showToast('加入自选股失败', 'error');
    }
}