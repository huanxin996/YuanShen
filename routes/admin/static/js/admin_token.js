// Token模态框相关JavaScript
let currentApiPath = '';
let modalCloseTimeout = null;
let isDragging = false;

async function openTokenModal(apiPath) {
    currentApiPath = apiPath;
    console.log('打开Token模态框:', apiPath);
    
    // 设置API路径
    const modalApiPathInput = document.getElementById('modalApiPath');
    const modalApiPathDisplay = document.getElementById('modalApiPathDisplay');
    
    if (modalApiPathInput) {
        modalApiPathInput.value = apiPath;
    }
    if (modalApiPathDisplay) {
        modalApiPathDisplay.textContent = apiPath;
    }
    
    // 显示加载状态
    showLoadingInModal();
    
    // 显示模态框并启动动画
    const modal = document.getElementById('tokenModal');
    if (modal) {
        // 清除之前的关闭超时
        if (modalCloseTimeout) {
            clearTimeout(modalCloseTimeout);
            modalCloseTimeout = null;
        }
        
        // 移除关闭动画类
        modal.classList.remove('closing');
        
        // 显示模态框
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // 强制重绘，然后添加显示类触发动画
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });
        
    } else {
        console.error('未找到Token模态框元素');
        alert('模态框初始化失败，请刷新页面重试');
        return;
    }
    
    // 获取当前token信息
    try {
        console.log('正在获取token信息...');
        const tokenInfo = await queryTokenInfo(apiPath);
        
        if (tokenInfo.success) {
            updateModalStatus(tokenInfo);
            updateCurrentTokenInfo(tokenInfo);
        } else {
            throw new Error(tokenInfo.error || '获取token信息失败');
        }
        
    } catch (error) {
        console.error('获取token信息失败:', error);
        showErrorInModal('获取token信息失败: ' + error.message);
    }
}

function closeTokenModal() {
    const modal = document.getElementById('tokenModal');
    if (modal && modal.style.display === 'block') {
        // 添加关闭动画类
        modal.classList.add('closing');
        modal.classList.remove('show');
        
        // 等待动画完成后隐藏模态框
        modalCloseTimeout = setTimeout(() => {
            modal.style.display = 'none';
            modal.classList.remove('closing');
            document.body.style.overflow = '';
            modalCloseTimeout = null;
        }, 300); // 与CSS动画时间保持一致
    }
    
    currentApiPath = '';
    
    // 延迟清除内容，避免在动画过程中闪烁
    setTimeout(() => {
        clearModalContent();
    }, 150);
}

/**
 * 查询Token信息
 * @param {string} apiPath - API路径
 * @returns {Promise<Object>} Token信息
 */
async function queryTokenInfo(apiPath) {
    const formData = new FormData();
    formData.append('api_path', apiPath);
    formData.append('query_type', 'info');
    
    const response = await fetch('/admin/token/query', {
        method: 'POST',
        body: formData
    });
    
    console.log('Token信息查询响应状态:', response.status);
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('获取到的token信息:', data);
    
    return data;
}

/**
 * 查询Token使用统计
 * @param {string} apiPath - API路径
 * @param {number} days - 查询天数
 * @returns {Promise<Object>} 使用统计
 */
async function queryTokenUsage(apiPath, days = 7) {
    const formData = new FormData();
    formData.append('api_path', apiPath);
    formData.append('query_type', 'usage');
    formData.append('days', days.toString());
    
    const response = await fetch('/admin/token/query', {
        method: 'POST',
        body: formData
    });
    
    console.log('Token使用统计查询响应状态:', response.status);
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('获取到的token使用统计:', data);
    
    return data;
}

function showLoadingInModal() {
    const statusElement = document.getElementById('modalCurrentStatus');
    const infoElement = document.getElementById('currentTokenInfo');
    
    if (statusElement) {
        statusElement.innerHTML = '<span class="badge loading"><i class="fas fa-spinner fa-spin"></i> 加载中...</span>';
    }
    
    if (infoElement) {
        infoElement.innerHTML = `
            <div class="info-section">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>正在获取配置信息...</p>
                </div>
            </div>
        `;
    }
    
    // 重置表单字段
    const customTokenInput = document.getElementById('customToken');
    const expireTimeInput = document.getElementById('expireTime');
    
    if (customTokenInput) customTokenInput.value = '';
    if (expireTimeInput) expireTimeInput.value = '3600000';
}

function showErrorInModal(errorMessage) {
    const statusElement = document.getElementById('modalCurrentStatus');
    const infoElement = document.getElementById('currentTokenInfo');
    
    if (statusElement) {
        statusElement.innerHTML = '<span class="badge" style="background: linear-gradient(135deg, #dc3545, #c82333); color: white;"><i class="fas fa-exclamation-triangle"></i> 获取失败</span>';
    }
    
    if (infoElement) {
        infoElement.innerHTML = `
            <div class="info-section">
                <h4 style="color: #dc3545;"><i class="fas fa-exclamation-triangle"></i> 错误信息</h4>
                <div style="color: #dc3545; background: linear-gradient(135deg, #f8d7da, #f5c6cb); padding: 15px; border-radius: 8px; border: 1px solid #f5c6cb; margin: 10px 0;">
                    ${errorMessage}
                </div>
                <button type="button" onclick="retryGetTokenInfo()" class="btn btn-secondary" style="margin-top: 15px;">
                    <i class="fas fa-redo"></i> 重试
                </button>
            </div>
        `;
    }
}

function clearModalContent() {
    const statusElement = document.getElementById('modalCurrentStatus');
    const infoElement = document.getElementById('currentTokenInfo');
    const customTokenInput = document.getElementById('customToken');
    const expireTimeInput = document.getElementById('expireTime');
    
    if (statusElement) statusElement.innerHTML = '';
    if (infoElement) infoElement.innerHTML = '';
    if (customTokenInput) customTokenInput.value = '';
    if (expireTimeInput) expireTimeInput.value = '3600000';
}

async function retryGetTokenInfo() {
    if (currentApiPath) {
        console.log('重试获取token信息:', currentApiPath);
        showLoadingInModal();
        try {
            const tokenInfo = await queryTokenInfo(currentApiPath);
            
            if (tokenInfo.success) {
                updateModalStatus(tokenInfo);
                updateCurrentTokenInfo(tokenInfo);
            } else {
                throw new Error(tokenInfo.error || '重试获取信息失败');
            }
            
        } catch (error) {
            console.error('重试获取token信息失败:', error);
            showErrorInModal('重试失败: ' + error.message);
        }
    }
}

function updateModalStatus(data) {
    const statusElement = document.getElementById('modalCurrentStatus');
    if (!statusElement) {
        console.error('未找到状态显示元素');
        return;
    }
    
    if (data.token_enabled) {
        if (data.has_custom_token) {
            statusElement.innerHTML = '<span class="badge custom"><i class="fas fa-check-circle"></i> 已启用 (自定义Token)</span>';
        } else {
            statusElement.innerHTML = '<span class="badge default"><i class="fas fa-shield-alt"></i> 已启用 (默认Token)</span>';
        }
    } else {
        statusElement.innerHTML = '<span class="badge disabled"><i class="fas fa-times-circle"></i> 未启用</span>';
    }
    
    // 更新表单字段
    const customTokenInput = document.getElementById('customToken');
    const expireTimeInput = document.getElementById('expireTime');
    
    if (customTokenInput) {
        customTokenInput.value = data.custom_token || '';
    }
    
    if (expireTimeInput) {
        expireTimeInput.value = data.expire_time_ms || 3600000;
    }
}

function updateCurrentTokenInfo(data) {
    const infoElement = document.getElementById('currentTokenInfo');
    if (!infoElement) {
        console.error('未找到信息显示元素');
        return;
    }
    
    let infoHtml = '<div class="info-section"><h4><i class="fas fa-info-circle"></i> 当前配置信息</h4>';
    
    if (data.token_enabled) {
        const currentToken = data.has_custom_token ? data.custom_token : data.default_token;
        const tokenDisplay = currentToken && currentToken.length > 20 ? 
            currentToken.substring(0, 20) + '...' : currentToken;
        
        infoHtml += `
            <p><strong>Token状态:</strong> <span class="text-success"><i class="fas fa-check-circle"></i> 已启用</span></p>
            <p><strong>当前Token:</strong> <code title="${currentToken || ''}">${tokenDisplay || '无'}</code></p>
            <p><strong>Token类型:</strong> <span style="font-weight: 500; color: ${data.has_custom_token ? '#28a745' : '#17a2b8'};">
                <i class="fas fa-${data.has_custom_token ? 'cog' : 'shield-alt'}"></i> ${data.has_custom_token ? '自定义' : '默认'}
            </span></p>
            <p><strong>过期时间:</strong> <span style="font-weight: 500;"><i class="fas fa-clock"></i> ${Math.round(data.expire_time_ms / 1000)} 秒</span></p>
        `;
        
        if (data.has_custom_token && currentToken) {
            infoHtml += `
                <div style="margin-top: 15px;">
                    <p><strong><i class="fas fa-key"></i> 完整Token:</strong></p>
                    <textarea readonly class="token-display-textarea">${currentToken}</textarea>
                </div>
            `;
        }
        
        // 添加使用统计查看按钮
        infoHtml += `
            <div style="margin-top: 20px;">
                <button type="button" onclick="showTokenUsageStats()" class="btn btn-info">
                    <i class="fas fa-chart-line"></i> 查看使用统计
                </button>
            </div>
        `;
    } else {
        infoHtml += `
            <p><strong>Token状态:</strong> <span class="text-danger"><i class="fas fa-times-circle"></i> 未启用</span></p>
            <div style="background: linear-gradient(135deg, #fff3cd, #ffeaa7); border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin-top: 15px;">
                <p style="margin: 0; color: #856404;">
                    <i class="fas fa-exclamation-triangle"></i> 
                    <strong>安全提醒：</strong>该API当前未启用Token验证，任何人都可以访问。建议启用Token验证以提高安全性。
                </p>
            </div>
        `;
    }
    
    infoHtml += '</div>';
    infoElement.innerHTML = infoHtml;
}

/**
 * 显示Token使用统计
 */
async function showTokenUsageStats(days = 7) {
    if (!currentApiPath) {
        alert('无法获取API路径信息');
        return;
    }
    
    try {
        // 显示加载状态
        const infoElement = document.getElementById('currentTokenInfo');
        if (infoElement) {
            const loadingHtml = `
                <div class="info-section">
                    <h4><i class="fas fa-chart-line"></i> 使用统计</h4>
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>正在加载使用统计...</p>
                    </div>
                </div>
            `;
            infoElement.innerHTML = loadingHtml;
        }
        
        // 查询使用统计
        const usageData = await queryTokenUsage(currentApiPath, days);
        
        if (usageData.success) {
            displayTokenUsageStats(usageData.usage_stats, days);
        } else {
            throw new Error(usageData.error || '获取使用统计失败');
        }
        
    } catch (error) {
        console.error('获取Token使用统计失败:', error);
        const infoElement = document.getElementById('currentTokenInfo');
        if (infoElement) {
            infoElement.innerHTML = `
                <div class="info-section">
                    <h4 style="color: #dc3545;"><i class="fas fa-exclamation-triangle"></i> 统计获取失败</h4>
                    <p style="color: #dc3545;">${error.message}</p>
                    <button type="button" onclick="retryGetTokenInfo()" class="btn btn-secondary">
                        <i class="fas fa-arrow-left"></i> 返回配置信息
                    </button>
                </div>
            `;
        }
    }
}

/**
 * 显示Token使用统计数据
 */
function displayTokenUsageStats(statsData, days) {
    const infoElement = document.getElementById('currentTokenInfo');
    if (!infoElement || !statsData) {
        return;
    }
    
    const stats = statsData.stats[currentApiPath];
    const summary = statsData.summary;
    
    let statsHtml = `
        <div class="info-section">
            <h4><i class="fas fa-chart-line"></i> Token使用统计 (近${days}天)</h4>
    `;
    
    if (stats) {
        const totalRequests = stats.total_success + stats.total_failure;
        const successRate = totalRequests > 0 ? ((stats.total_success / totalRequests) * 100).toFixed(1) : '0';
        
        statsHtml += `
            <div style="background: linear-gradient(135deg, #f8f9fa, #ffffff); padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #e9ecef;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; text-align: center;">
                    <div>
                        <div style="color: #28a745; font-size: 1.5em; font-weight: bold;"><i class="fas fa-check-circle"></i> ${stats.total_success}</div>
                        <div style="color: #6c757d; font-size: 0.9em;">成功次数</div>
                    </div>
                    <div>
                        <div style="color: #dc3545; font-size: 1.5em; font-weight: bold;"><i class="fas fa-times-circle"></i> ${stats.total_failure}</div>
                        <div style="color: #6c757d; font-size: 0.9em;">失败次数</div>
                    </div>
                    <div>
                        <div style="color: #17a2b8; font-size: 1.5em; font-weight: bold;"><i class="fas fa-percentage"></i> ${successRate}%</div>
                        <div style="color: #6c757d; font-size: 0.9em;">成功率</div>
                    </div>
                </div>
            </div>
        `;
        
        // 显示每日统计
        if (Object.keys(stats.dates).length > 0) {
            statsHtml += '<h5><i class="fas fa-calendar-alt"></i> 每日统计明细:</h5>';
            statsHtml += '<div style="max-height: 200px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 8px; background: #fff;">';
            statsHtml += '<table style="width: 100%; font-size: 13px; border-collapse: collapse;">';
            statsHtml += '<thead><tr style="background: linear-gradient(135deg, #e9ecef, #f8f9fa);"><th style="padding: 8px; border: 1px solid #dee2e6;">日期</th><th style="padding: 8px; border: 1px solid #dee2e6;">成功</th><th style="padding: 8px; border: 1px solid #dee2e6;">失败</th><th style="padding: 8px; border: 1px solid #dee2e6;">总计</th></tr></thead>';
            statsHtml += '<tbody>';
            
            for (const [date, dayStats] of Object.entries(stats.dates)) {
                statsHtml += `
                    <tr style="transition: background-color 0.2s ease;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;">${date}</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; color: #28a745; font-weight: 500;">${dayStats.success}</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; color: #dc3545; font-weight: 500;">${dayStats.failure}</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; font-weight: bold;">${dayStats.total}</td>
                    </tr>
                `;
            }
            
            statsHtml += '</tbody></table></div>';
        } else {
            statsHtml += '<p style="color: #6c757d; font-style: italic; text-align: center; padding: 20px;"><i class="fas fa-info-circle"></i> 暂无详细的每日统计数据</p>';
        }
    } else {
        statsHtml += '<div style="text-align: center; padding: 30px; color: #6c757d;"><i class="fas fa-chart-line" style="font-size: 3em; margin-bottom: 15px; opacity: 0.3;"></i><p style="font-style: italic;">该API暂无Token使用记录</p></div>';
    }
    
    statsHtml += `
        <div style="margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap;">
            <button type="button" onclick="retryGetTokenInfo()" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> 返回配置信息
            </button>
            <button type="button" onclick="showTokenUsageStats(30)" class="btn btn-info">
                <i class="fas fa-calendar"></i> 查看30天统计
            </button>
        </div>
        </div>
    `;
    
    infoElement.innerHTML = statsHtml;
}

function generateRandomToken() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let token = '';
    for (let i = 0; i < 32; i++) {
        token += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    const customTokenInput = document.getElementById('customToken');
    if (customTokenInput) {
        customTokenInput.value = token;
        // 添加视觉反馈
        customTokenInput.style.background = 'linear-gradient(135deg, #d4edda, #c3e6cb)';
        customTokenInput.style.borderColor = '#28a745';
        customTokenInput.style.transition = 'all 0.3s ease';
        
        setTimeout(() => {
            customTokenInput.style.background = '#fff';
            customTokenInput.style.borderColor = '#e9ecef';
        }, 2000);
        
        console.log('已生成新的随机Token:', token);
    } else {
        console.error('未找到自定义Token输入框');
        alert('无法生成Token，请刷新页面重试');
    }
}

function setTokenAction(action) {
    const tokenActionInput = document.getElementById('tokenAction');
    if (!tokenActionInput) {
        alert('表单元素未找到，请刷新页面重试');
        return;
    }
    
    tokenActionInput.value = action;
    
    // 根据不同操作显示确认信息
    let confirmMessage = '';
    const customToken = document.getElementById('customToken')?.value || '';
    
    switch (action) {
        case 'enable':
            if (customToken) {
                confirmMessage = `✅ 确定要启用Token验证并设置自定义Token吗？\n\n🔑 Token: ${customToken.substring(0, 20)}${customToken.length > 20 ? '...' : ''}\n\n这将替换当前的Token配置。`;
            } else {
                confirmMessage = '✅ 确定要启用Token验证吗？\n\n将使用系统默认Token进行验证。';
            }
            break;
        case 'disable':
            confirmMessage = '❌ 确定要禁用Token验证吗？\n\n⚠️ 警告：这将允许任何人无需token访问此API！\n\n这可能存在安全风险，请谨慎操作。';
            break;
        case 'set_custom':
            if (!customToken) {
                alert('❌ 请先输入自定义Token！');
                return;
            }
            confirmMessage = `🔧 确定要设置自定义Token吗？\n\n🔑 Token: ${customToken.substring(0, 20)}${customToken.length > 20 ? '...' : ''}\n\n这将替换当前Token配置。`;
            break;
        case 'generate':
            confirmMessage = '🎲 确定要生成新的随机Token吗？\n\n⚠️ 注意：这将替换当前Token配置，现有的Token将失效。';
            break;
        case 'remove_custom':
            confirmMessage = '🔄 确定要移除自定义Token并使用默认Token吗？\n\n将恢复使用系统默认Token配置。';
            break;
        default:
            confirmMessage = '确定要执行此操作吗？';
    }
    
    if (confirm(confirmMessage)) {
        const form = document.getElementById('tokenForm');
        if (form) {
            // 显示提交状态
            showSubmittingState();
            console.log('提交Token操作:', action, '路径:', currentApiPath);
            form.submit();
        } else {
            alert('表单未找到，请刷新页面重试');
        }
    }
}

function showSubmittingState() {
    const buttons = document.querySelectorAll('.button-group .btn');
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.6';
        btn.style.cursor = 'not-allowed';
        btn.style.transform = 'none';
    });
    
    const statusElement = document.getElementById('modalCurrentStatus');
    if (statusElement) {
        statusElement.innerHTML = '<span class="badge" style="background: linear-gradient(135deg, #17a2b8, #6f42c1); color: white;"><i class="fas fa-spinner fa-spin"></i> 处理中...</span>';
    }
    
    const infoElement = document.getElementById('currentTokenInfo');
    if (infoElement) {
        infoElement.innerHTML = `
            <div class="info-section">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>正在处理您的请求，请稍候...</p>
                </div>
            </div>
        `;
    }
}

// 设置模态框事件监听器
function setupModalEvents() {
    // 点击模态框外部关闭 - 优化事件处理
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('tokenModal');
        if (event.target === modal && !isDragging) {
            closeTokenModal();
        }
    });
    
    // ESC键关闭模态框
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modal = document.getElementById('tokenModal');
            if (modal && modal.classList.contains('show')) {
                closeTokenModal();
            }
        }
    });
    
    // 防止文本选择时误触关闭模态框
    document.addEventListener('selectstart', function(event) {
        if (event.target.closest('.modal-content')) {
            isDragging = true;
            setTimeout(() => {
                isDragging = false;
            }, 100);
        }
    });
    
    // 监听鼠标拖拽事件
    document.addEventListener('mousedown', function(event) {
        if (event.target.closest('.token-display-textarea, .info-section code, .api-path-display')) {
            isDragging = false;
        }
    });
    
    document.addEventListener('mousemove', function(event) {
        if (event.buttons === 1 && event.target.closest('.modal-content')) {
            isDragging = true;
        }
    });
    
    document.addEventListener('mouseup', function() {
        setTimeout(() => {
            isDragging = false;
        }, 50);
    });
}

// 页面加载完成后初始化
function initializeTokenModal() {
    console.log('初始化Token模态框...');
    
    // 检查是否存在必要的DOM元素
    const requiredElements = ['tokenModal', 'modalApiPath', 'tokenAction', 'tokenForm'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.warn('Token模态框缺少必要元素:', missingElements);
        return false;
    }
    
    // 设置事件监听器
    setupModalEvents();
    
    console.log('Token模态框初始化完成');
    return true;
}

// 页面加载完成后自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTokenModal);
} else {
    initializeTokenModal();
}

// 导出函数供全局使用
window.openTokenModal = openTokenModal;
window.closeTokenModal = closeTokenModal;
window.generateRandomToken = generateRandomToken;
window.setTokenAction = setTokenAction;
window.showTokenUsageStats = showTokenUsageStats;