// 新闻管理类
class NewsManager {
    constructor() {
        this.news = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.pageSize = 20;
        this.currentCategory = 'all';
        this.searchQuery = '';
        this.viewMode = 'grid';
        this.loading = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadNews();
        this.loadCategories();
    }

    bindEvents() {
        // 分类导航事件
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchCategory(link.dataset.category);
            });
        });

        // 搜索事件
        const searchBtn = document.getElementById('searchBtn');
        const searchInput = document.getElementById('searchInput');
        
        searchBtn.addEventListener('click', () => this.handleSearch());
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSearch();
        });

        // 刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshNews();
        });

        // 视图切换
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.switchView(btn.dataset.view);
            });
        });

        // 分页事件
        document.getElementById('prevPage').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.goToPage(this.currentPage - 1);
            }
        });

        document.getElementById('nextPage').addEventListener('click', () => {
            if (this.currentPage < this.totalPages) {
                this.goToPage(this.currentPage + 1);
            }
        });

        // 新闻卡片点击事件（事件委托）
        document.getElementById('newsContainer').addEventListener('click', (e) => {
            const card = e.target.closest('.news-card');
            if (card) {
                const newsId = card.dataset.id;
                this.showNewsDetail(newsId);
            }
        });
    }

    async loadNews(category = 'all', page = 1) {
        if (!window.API) {
            setTimeout(() => this.loadNews(category, page), 100);
            return;
        }
        this.setLoading(true);
        
        try {
            const response = await window.API.getNews(
                this.currentCategory,
                this.currentPage,
                this.pageSize,
                this.searchQuery
            );
            
            this.news = response;
            this.renderNews();
            this.updatePagination();
            
        } catch (error) {
            console.error('加载新闻失败:', error);
            this.showError('加载新闻失败，请稍后重试');
        } finally {
            this.setLoading(false);
        }
    }

    async loadCategories() {
        try {
            const categories = await window.API.getCategoryTree();
            this.renderCategoryTree(categories);
        } catch (error) {
            console.error('加载分类失败:', error);
        }
    }

    renderNews() {
        const container = document.getElementById('newsContainer');
        
        if (this.news.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-newspaper"></i>
                    <p>暂无新闻内容</p>
                </div>
            `;
            return;
        }

        const newsHTML = this.news.map(news => this.createNewsCard(news)).join('');
        container.innerHTML = newsHTML;
        container.className = `news-container ${this.viewMode}-view`;
    }

    createNewsCard(news) {
        const publishTime = this.formatTime(news.publish_time);
        const tagsHTML = news.tags.map(tag => `<span class="news-tag">${tag}</span>`).join('');
        
        return `
            <div class="news-card" data-id="${news.id}">
                <div class="news-card-header">
                    <h3 class="news-title">${news.title}</h3>
                    <span class="news-category">${news.category}</span>
                </div>
                <p class="news-content">${news.content}</p>
                <div class="news-meta">
                    <span class="news-source">${news.source}</span>
                    <span class="news-time">${publishTime}</span>
                </div>
                <div class="news-tags">${tagsHTML}</div>
            </div>
        `;
    }

    renderCategoryTree(categories) {
        const container = document.getElementById('categoryTree');
        
        const renderTree = (items, level = 0) => {
            return items.map(item => `
                <div class="tree-item ${level > 0 ? 'tree-indent' : ''}" 
                     data-category="${item.name}"
                     style="padding-left: ${12 + level * 16}px">
                    <i class="fas fa-${level === 0 ? 'folder' : 'file'}"></i>
                    <span>${item.name}</span>
                    ${item.children && item.children.length > 0 ? `(${item.children.length})` : ''}
                </div>
                ${item.children ? renderTree(item.children, level + 1) : ''}
            `).join('');
        };

        container.innerHTML = renderTree(categories);
        
        // 绑定分类点击事件
        container.querySelectorAll('.tree-item').forEach(item => {
            item.addEventListener('click', () => {
                const category = item.dataset.category;
                this.switchCategory(category);
            });
        });
    }

    switchCategory(category) {
        // 更新导航状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.category === category) {
                link.classList.add('active');
            }
        });

        // 更新分类树状态
        document.querySelectorAll('.tree-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.category === category) {
                item.classList.add('active');
            }
        });

        this.currentCategory = category;
        this.currentPage = 1;
        this.updateSectionTitle();
        this.loadNews();
    }

    handleSearch() {
        const searchInput = document.getElementById('searchInput');
        this.searchQuery = searchInput.value.trim();
        this.currentPage = 1;
        this.loadNews();
    }

    switchView(view) {
        this.viewMode = view;
        
        // 更新按钮状态
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        
        // 重新渲染新闻
        this.renderNews();
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadNews();
    }

    updatePagination() {
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        const pageInfo = document.getElementById('pageInfo');
        
        prevBtn.disabled = this.currentPage === 1;
        nextBtn.disabled = this.currentPage >= this.totalPages;
        pageInfo.textContent = `第 ${this.currentPage} 页`;
    }

    updateSectionTitle() {
        const title = document.getElementById('sectionTitle');
        if (this.currentCategory === 'all') {
            title.textContent = '最新新闻';
        } else {
            title.textContent = `${this.currentCategory} 新闻`;
        }
    }

    async showNewsDetail(newsId) {
        try {
            const news = await window.API.getNewsById(newsId);
            this.showNewsModal(news);
        } catch (error) {
            console.error('获取新闻详情失败:', error);
            this.showError('获取新闻详情失败');
        }
    }

    showNewsModal(news) {
        const modal = document.getElementById('newsModal');
        
        document.getElementById('modalTitle').textContent = news.title;
        document.getElementById('modalAuthor').textContent = `作者: ${news.author}`;
        document.getElementById('modalDate').textContent = `发布时间: ${news.publish_time}`;
        document.getElementById('modalSource').textContent = `来源: ${news.source}`;
        document.getElementById('modalCategory').textContent = news.category;
        document.getElementById('modalContent').innerHTML = news.content.replace(/\n/g, '<br>');
        document.getElementById('modalLink').href = news.url;
        
        // 渲染标签
        const tagsContainer = document.getElementById('modalTags');
        tagsContainer.innerHTML = news.tags.map(tag => 
            `<span class="news-tag">${tag}</span>`
        ).join('');
        
        modal.classList.add('show');
        
        // 绑定关闭事件
        document.getElementById('closeModal').onclick = () => {
            modal.classList.remove('show');
        };
        
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        };
    }

    refreshNews() {
        this.loadNews();
        this.showSuccess('新闻已刷新');
    }

    setLoading(loading) {
        this.loading = loading;
        const container = document.getElementById('newsContainer');
        
        if (loading) {
            container.innerHTML = `
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>正在加载新闻...</p>
                </div>
            `;
        }
    }

    formatTime(timeString) {
        const date = new Date(timeString);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) {
            return '刚刚';
        } else if (diff < 3600000) {
            return `${Math.floor(diff / 60000)} 分钟前`;
        } else if (diff < 86400000) {
            return `${Math.floor(diff / 3600000)} 小时前`;
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // 统一委托给 UIManager，避免重复实现与空元素问题
        if (window.UIManager && typeof window.UIManager.showNotification === 'function') {
            window.UIManager.showNotification(message, type, 3000);
            return;
        }
        // 后备：简单创建并显示通知（仅在 UIManager 不可用时）
        let notification = document.getElementById('notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.className = 'notification';
            notification.innerHTML = `
                <div class="notification-content">
                    <i class="notification-icon"></i>
                    <span class="notification-text"></span>
                </div>
            `;
            (document.getElementById('app') || document.body).appendChild(notification);
        }
        const icon = notification.querySelector('.notification-icon');
        const text = notification.querySelector('.notification-text');
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        icon.className = iconMap[type] || iconMap.info;
        text.textContent = message;
        notification.className = `notification ${type} show`;
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
}

// 创建新闻管理器实例
document.addEventListener('DOMContentLoaded', () => {
    window.NewsManager = new NewsManager();
});