// 主应用类
class NewsApp {
    constructor() {
        this.initialized = false;
        this.hotTopics = ['人工智能', '区块链', '元宇宙', '新能源', '生物医药'];
        
        this.init();
    }

    async waitForAPI() {
        return new Promise(resolve => {
            const checkAPI = () => {
                if (window.API) {
                    resolve();
                } else {
                    setTimeout(checkAPI, 100);
                }
            };
            checkAPI();
        });
    }

    async init() {
        // 等待API对象可用
        await this.waitForAPI();

        try {
            // 检查API连接
            await this.checkAPIConnection();
            
            // 初始化各个模块
            await this.initializeModules();
            
            // 加载初始数据
            await this.loadInitialData();
            
            // 设置定时刷新
            this.setupAutoRefresh();
            
            this.initialized = true;
            console.log('新闻快讯应用初始化完成');
            
        } catch (error) {
            console.error('应用初始化失败:', error);
            this.showInitError(error);
        }
    }

    async checkAPIConnection() {
        try {
            const health = await window.API.healthCheck();
            console.log('API连接正常:', health);
            
            if (window.UIManager) {
                window.UIManager.showNotification('API连接成功', 'success', 2000);
            }
            
        } catch (error) {
            console.warn('API连接失败:', error);
            
            if (window.UIManager) {
                window.UIManager.showNotification(
                    'API连接失败，部分功能可能无法使用', 
                    'warning', 
                    5000
                );
            }
            
            // 继续初始化，使用本地数据
            return false;
        }
        
        return true;
    }

    async initializeModules() {
        // 确保所有模块都已初始化
        if (!window.NewsManager) {
            console.warn('NewsManager未初始化，创建实例...');
            window.NewsManager = new NewsManager();
        }
        
        if (!window.CategoryManager) {
            console.warn('CategoryManager未初始化，创建实例...');
            window.CategoryManager = new CategoryManager();
        }
        
        if (!window.UIManager) {
            console.warn('UIManager未初始化，创建实例...');
            window.UIManager = new UIManager();
        }
    }

    async loadInitialData() {
        // 加载热门话题
        if (window.UIManager) {
            window.UIManager.updateHotTopics(this.hotTopics);
        }
        
        // 尝试加载实时数据
        try {
            // 新闻数据通过NewsManager自动加载
            // 分类数据通过CategoryManager自动加载
            
            console.log('初始数据加载完成');
            
        } catch (error) {
            console.warn('部分数据加载失败:', error);
            
            // 使用本地示例数据
            this.loadSampleData();
        }
    }

    loadSampleData() {
        // 如果API不可用，加载示例数据
        console.log('加载示例数据...');
        
        if (window.NewsManager && !window.NewsManager.news.length) {
            const sampleNews = [
                {
                    id: '1',
                    title: '百度发布新AI产品',
                    content: '百度公司今日发布了最新的人工智能产品，引起了业界广泛关注。这款产品采用了最新的深度学习技术，在自然语言处理方面取得了重大突破。',
                    publish_time: '2024-01-15 10:00:00',
                    author: '张三',
                    source: 'baidu.com',
                    url: 'https://www.baidu.com/news/1',
                    category: '科技',
                    tags: ['AI', '百度', '人工智能']
                },
                {
                    id: '2',
                    title: '科技行业迎来新突破',
                    content: '最新研究显示，科技行业在人工智能领域取得了重大突破。多家科技公司宣布在机器学习、计算机视觉等领域取得重要进展。',
                    publish_time: '2024-01-14 15:30:00',
                    author: '李四',
                    source: 'tech.sina.com',
                    url: 'https://tech.sina.com/news/2',
                    category: '科技',
                    tags: ['科技', '突破', 'AI']
                }
            ];
            
            window.NewsManager.news = sampleNews;
            window.NewsManager.renderNews();
        }
        
        if (window.CategoryManager && !window.CategoryManager.categories.length) {
            const sampleCategories = [
                {
                    id: '1',
                    name: '科技',
                    children: [
                        { id: '5', name: '人工智能', children: [] },
                        { id: '6', name: '区块链', children: [] }
                    ]
                },
                { id: '2', name: '财经', children: [] },
                { id: '3', name: '体育', children: [] },
                { id: '4', name: '娱乐', children: [] }
            ];
            
            window.CategoryManager.categories = sampleCategories;
            window.CategoryManager.renderCategoryTree();
        }
    }

    setupAutoRefresh() {
        // 每5分钟自动刷新一次
        setInterval(() => {
            if (window.NewsManager) {
                window.NewsManager.refreshNews();
            }
        }, 5 * 60 * 1000);
        
        console.log('自动刷新已设置: 每5分钟');
    }

    showInitError(error) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;
        
        const contentDiv = document.createElement('div');
        contentDiv.style.cssText = `
            background: white;
            padding: 32px;
            border-radius: 12px;
            max-width: 500px;
            text-align: center;
        `;
        
        contentDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="
                font-size: 48px;
                color: #ef4444;
                margin-bottom: 16px;
            "></i>
            <h3 style="margin-bottom: 16px; color: #1e293b;">应用初始化失败</h3>
            <p style="color: #64748b; margin-bottom: 24px;">
                ${error.message || '请检查网络连接和API服务状态'}
            </p>
            <button onclick="location.reload()" style="
                background: #2563eb;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
            ">重新加载</button>
        `;
        
        errorDiv.appendChild(contentDiv);
        document.body.appendChild(errorDiv);
    }

    // 全局方法
    static showNotification(message, type = 'info', duration = 3000) {
        if (window.UIManager) {
            window.UIManager.showNotification(message, type, duration);
        }
    }

    static showLoading(message = '加载中...') {
        if (window.UIManager) {
            window.UIManager.showLoading(message);
        }
    }

    static hideLoading() {
        if (window.UIManager) {
            window.UIManager.hideLoading();
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NewsApp();
});

// 全局错误处理
window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error);
    NewsApp.showNotification('发生未知错误，请刷新页面重试', 'error');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason);
    NewsApp.showNotification('网络请求失败，请检查连接', 'error');
});