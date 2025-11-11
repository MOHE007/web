// UI 管理类
class UIManager {
    constructor() {
        this.modals = {};
        this.notifications = [];
        // 确保在 DOM 就绪后再初始化，避免元素尚未存在导致的空引用
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.bindEvents();
        this.setupModals();
        this.setupFloatingButtons();
    }

    bindEvents() {
        // 模态框关闭事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
            if (e.target.classList.contains('close-btn')) {
                const modal = e.target.closest('.modal');
                if (modal) this.closeModal(modal.id);
            }
        });

        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });

        // 浮动按钮事件
        document.getElementById('processUrlBtn').addEventListener('click', () => {
            this.openProcessModal();
        });

        document.getElementById('addNewsBtn').addEventListener('click', () => {
            this.openAddNewsModal();
        });

        // 处理新闻按钮
        document.getElementById('processNewsBtn').addEventListener('click', () => {
            this.processNews();
        });
    }

    setupModals() {
        this.modals = {
            news: document.getElementById('newsModal'),
            process: document.getElementById('processModal')
        };
    }

    setupFloatingButtons() {
        const mainFab = document.getElementById('mainFab');
        const fabContainer = document.querySelector('.fab-container');
        
        mainFab.addEventListener('click', () => {
            fabContainer.classList.toggle('active');
        });

        // 点击其他地方关闭浮动菜单
        document.addEventListener('click', (e) => {
            if (!fabContainer.contains(e.target)) {
                fabContainer.classList.remove('active');
            }
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.style.overflow = '';
    }

    openProcessModal() {
        this.openModal('processModal');
    }

    openAddNewsModal() {
        // 这里可以实现添加新闻的模态框
        this.showNotification('添加新闻功能开发中...', 'info');
    }

    async processNews() {
        const url = document.getElementById('newsUrl').value.trim();
        const processType = document.querySelector('input[name="processType"]:checked').value;
        
        if (!url) {
            this.showNotification('请输入新闻URL', 'warning');
            return;
        }

        if (!this.isValidUrl(url)) {
            this.showNotification('请输入有效的URL', 'error');
            return;
        }

        const processBtn = document.getElementById('processNewsBtn');
        const originalText = processBtn.innerHTML;
        
        // 显示加载状态
        processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
        processBtn.disabled = true;

        try {
            const result = await window.API.processNews(url, processType);
            
            this.showNotification('新闻处理成功！', 'success');
            this.closeModal('processModal');
            
            // 清空表单
            document.getElementById('newsUrl').value = '';
            
            // 刷新新闻列表
            if (window.NewsManager) {
                window.NewsManager.refreshNews();
            }
            
            // 显示处理结果
            console.log('处理结果:', result);
            
        } catch (error) {
            console.error('处理新闻失败:', error);
            this.showNotification('处理新闻失败，请检查URL是否正确', 'error');
        } finally {
            // 恢复按钮状态
            processBtn.innerHTML = originalText;
            processBtn.disabled = false;
        }
    }

    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    showNotification(message, type = 'info', duration = 3000) {
        try {
        let notification = document.getElementById('notification');
        // 若通知容器不存在，则动态创建，避免空元素导致的报错
        if (!notification) {
            const appRoot = document.getElementById('app') || document.body;
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.className = 'notification';
            notification.innerHTML = `
                <div class="notification-content">
                    <i class="notification-icon"></i>
                    <span class="notification-text"></span>
                </div>
            `;
            appRoot.appendChild(notification);
        }

        let icon = notification.querySelector('.notification-icon');
        let text = notification.querySelector('.notification-text');
        // 容错：若内部结构缺失，补齐元素
        if (!icon) {
            icon = document.createElement('i');
            icon.className = 'notification-icon';
            notification.querySelector('.notification-content')?.insertAdjacentElement('afterbegin', icon);
        }
        if (!text) {
            text = document.createElement('span');
            text.className = 'notification-text';
            notification.querySelector('.notification-content')?.appendChild(text);
        }

        // 设置图标和样式
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        const colorMap = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#2563eb'
        };
        
        if (!icon || !text) {
            console.warn('notification元素结构缺失，跳过通知显示');
            return;
        }
        icon.className = iconMap[type] || iconMap.info;
        icon.style.color = colorMap[type] || colorMap.info;
        text.textContent = message;
        
        // 显示通知
        notification.className = `notification show ${type}`;
        
        // 自动隐藏
        setTimeout(() => {
            notification.classList.remove('show');
        }, duration);
        } catch (e) {
            console.warn('显示通知时发生异常:', e);
        }
    }

    showLoading(message = '加载中...') {
        const loadingHTML = `
            <div class="loading-overlay">
                <div class="loading-content">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>${message}</p>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', loadingHTML);
    }

    hideLoading() {
        const loading = document.querySelector('.loading-overlay');
        if (loading) {
            loading.remove();
        }
    }

    updateHotTopics(topics) {
        const container = document.getElementById('hotTopics');
        
        if (!topics || topics.length === 0) {
            container.innerHTML = '<p class="text-muted">暂无热门话题</p>';
            return;
        }
        
        const topicsHTML = topics.map(topic => `
            <div class="topic-item" data-topic="${topic}">
                <i class="fas fa-fire"></i>
                <span>${topic}</span>
            </div>
        `).join('');
        
        container.innerHTML = topicsHTML;
        
        // 绑定点击事件
        container.querySelectorAll('.topic-item').forEach(item => {
            item.addEventListener('click', () => {
                const topic = item.dataset.topic;
                this.handleTopicClick(topic);
            });
        });
    }

    handleTopicClick(topic) {
        // 搜索相关新闻
        const searchInput = document.getElementById('searchInput');
        searchInput.value = topic;
        
        if (window.NewsManager) {
            window.NewsManager.handleSearch();
        }
        
        this.showNotification(`正在搜索 "${topic}" 相关新闻`, 'info');
    }
}

// 创建 UI 管理器实例
window.UIManager = new UIManager();