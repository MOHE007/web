// API 配置
const API_BASE_URL = 'http://127.0.0.1:8000';

// API 请求封装
class API {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // 新闻相关 API
    async getNews(category = null, page = 1, limit = 20, search = '') {
        const params = new URLSearchParams();
        if (category && category !== 'all') params.append('category', category);
        if (page > 1) params.append('page', page);
        if (limit !== 20) params.append('limit', limit);
        if (search) params.append('search', search);
        
        return this.request(`/news?${params.toString()}`);
    }

    async getNewsById(id) {
        return this.request(`/news/${id}`);
    }

    async createNews(newsData) {
        return this.request('/news', {
            method: 'POST',
            body: JSON.stringify(newsData)
        });
    }

    async updateNews(id, newsData) {
        return this.request(`/news/${id}`, {
            method: 'PUT',
            body: JSON.stringify(newsData)
        });
    }

    async deleteNews(id) {
        return this.request(`/news/${id}`, {
            method: 'DELETE'
        });
    }

    // 分类相关 API
    async getCategories() {
        return this.request('/categories');
    }

    async getCategoryTree() {
        return this.request('/categories/tree');
    }

    async getCategoryById(id) {
        return this.request(`/categories/${id}`);
    }

    async createCategory(categoryData) {
        return this.request('/categories', {
            method: 'POST',
            body: JSON.stringify(categoryData)
        });
    }

    // 新闻处理 API
    async processNews(url, type = 'full') {
        const endpointMap = {
            'full': '/process-news',
            'collect': '/process-news',
            'parse': '/process-news',
            'clean': '/process-news'
        };
        
        return this.request(endpointMap[type], {
            method: 'POST',
            body: JSON.stringify({ url })
        });
    }

    // 健康检查
    async healthCheck() {
        return this.request('/health');
    }
}

// 创建 API 实例
const api = new API();

// 导出 API 实例
window.API = api;