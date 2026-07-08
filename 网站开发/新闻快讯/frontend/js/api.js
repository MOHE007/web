// API 配置
const API_BASE_URL = (() => {
    try {
        const override = typeof window !== 'undefined' ? window.__API_BASE__ : null;
        if (override && typeof override === 'string' && override.trim().length > 0) {
            return override.trim();
        }
        const host = (typeof location !== 'undefined' && location.hostname) ? location.hostname : '';
        if (host === 'localhost' || host === '127.0.0.1') {
            return 'http://127.0.0.1:8000';
        }
        return 'https://api.wakolanews.online';
    } catch (_) {
        return 'http://127.0.0.1:8000';
    }
})();

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

        // DNS 不通时静默降级，不抛到控制台
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), 5000);
        try {
            const response = await fetch(url, { ...config, signal: controller.signal });
            clearTimeout(id);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (_) {
            clearTimeout(id);
            return null;
        }
    }

    // 获取新闻列表
    async getNews(page = 1, limit = 50) {
        const params = new URLSearchParams();
        if (page > 1) params.append('page', page);
        if (limit !== 20) params.append('limit', limit);
        return this.request(`/news?${params.toString()}`);
    }

    // 获取高分新闻
    async getTopNews(minScore = 5.0, limit = 50) {
        const params = new URLSearchParams();
        params.append('min_score', minScore);
        params.append('limit', limit);
        return this.request(`/news/top?${params.toString()}`);
    }

    // 导入 Google News
    async importGoogleNews(lang = 'zh', limit = 30) {
        const params = new URLSearchParams();
        params.append('lang', lang);
        params.append('limit', limit);
        params.append('score', 'true');
        return this.request(`/news/import/google_news?${params.toString()}`);
    }

    // 导入 News Minimalist
    async importNewsMinimalist(limit = 30) {
        const params = new URLSearchParams();
        params.append('limit', limit);
        return this.request(`/news/import/newsminimalist?${params.toString()}`);
    }

    // 健康检查
    async healthCheck() {
        return this.request('/health');
    }
}

// 创建全局 API 实例
window.API = new API();
