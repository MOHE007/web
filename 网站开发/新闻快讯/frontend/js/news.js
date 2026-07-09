// 新闻管理 — 直接读取 news.json（GitHub Actions 定时生成）
class NewsManager {
    constructor() {
        this.items = [];
        this.feedEl = null;
        this.init();
    }

    async init() {
        this.feedEl = document.getElementById('news-feed');
        if (!this.feedEl) return;
        this.renderLoading();
        await this.loadNews();
        this.startAutoRefresh();
    }

    // ── 数据加载 ──────────────────────────────────────────

    async loadNews() {
        this.renderLoading();
        let newsData = [];

        // 1. 尝试读取 news.json
        try {
            const resp = await fetch('/news.json?_t=' + Date.now());
            if (resp.ok) {
                const data = await resp.json();
                if (Array.isArray(data)) {
                    newsData = data;
                }
            }
        } catch (_) {
            // 静默降级
        }

        // 2. 无数据则用示例
        if (newsData.length === 0) {
            newsData = this.getSampleNews();
        }

        this.items = newsData;
        this.render();
    }

    // ── 渲染 ──────────────────────────────────────────────

    render() {
        if (this.items.length === 0) {
            this.feedEl.innerHTML = '<div class="empty-state"><p>暂无新闻</p></div>';
            return;
        }

        // 按 significance_score 降序
        const sorted = [...this.items].sort((a, b) => {
            const sa = a.significance_score ?? 0;
            const sb = b.significance_score ?? 0;
            return sb - sa;
        });

        this.feedEl.innerHTML = sorted.map(item => this.renderItem(item)).join('');
    }

    renderItem(item) {
        const score = item.significance_score ?? null;
        const scoreClass = score !== null ? this.scoreClass(score) : 'no-score';
        const scoreDot = score !== null
            ? `<span class="score-dot ${scoreClass}" title="重要性: ${score}"></span>`
            : '';

        const title = this.escapeHtml(item.title || '无标题');
        const url = item.url || '#';
        const source = this.escapeHtml(item.source || '未知来源');
        const timeStr = this.formatTime(item.publish_time);

        return `
            <div class="news-item">
                <a href="${url}" class="news-link" target="_blank" rel="noopener noreferrer">
                    ${scoreDot}
                    <span class="news-title">${title}</span>
                </a>
                <div class="news-meta">
                    <span>${source}</span>
                    ${timeStr ? ` <span>·</span> <span>${timeStr}</span>` : ''}
                </div>
            </div>
        `;
    }

    renderLoading() {
        this.feedEl.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>正在加载新闻...</p>
            </div>
        `;
    }

    // ── 自动刷新 ──────────────────────────────────────────

    startAutoRefresh() {
        setInterval(() => {
            this.loadNews();
        }, 5 * 60 * 1000);
    }

    // ── 工具函数 ──────────────────────────────────────────

    scoreClass(score) {
        return `score-${Math.max(0, Math.min(10, Math.round(score)))}`;
    }

    formatTime(timeStr) {
        if (!timeStr) return '';
        try {
            const date = new Date(timeStr);
            const now = new Date();
            const diff = now - date;
            if (diff < 0) return '';
            if (diff < 60000) return '刚刚';
            if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
            if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
            if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`;
            return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
        } catch (_) {
            return timeStr;
        }
    }

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ── 示例数据 ──────────────────────────────────────────

    getSampleNews() {
        return [
            { "title": "中国成功发射新一代载人飞船 开启深空探测新篇章", "source": "新华网", "publish_time": new Date(Date.now() - 30*60000).toISOString(), "significance_score": 8.7, "url": "#" },
            { "title": "全球AI峰会在北京开幕 多国领导人出席", "source": "人民网", "publish_time": new Date(Date.now() - 120*60000).toISOString(), "significance_score": 8.2, "url": "#" },
            { "title": "世卫组织宣布新型疫苗研发取得重大突破", "source": "Reuters", "publish_time": new Date(Date.now() - 180*60000).toISOString(), "significance_score": 7.9, "url": "#" },
            { "title": "央行宣布降准0.5个百分点 释放长期资金约1万亿", "source": "财经网", "publish_time": new Date(Date.now() - 240*60000).toISOString(), "significance_score": 7.5, "url": "#" },
            { "title": "国际空间站新模块成功对接 中国实验舱投入使用", "source": "BBC News", "publish_time": new Date(Date.now() - 360*60000).toISOString(), "significance_score": 7.1, "url": "#" },
            { "title": "欧盟通过新气候法案 2030年碳排放减半", "source": "Reuters", "publish_time": new Date(Date.now() - 480*60000).toISOString(), "significance_score": 6.8, "url": "#" },
            { "title": "新型量子计算机运算速度创纪录 超越经典超算", "source": "科技日报", "publish_time": new Date(Date.now() - 600*60000).toISOString(), "significance_score": 6.4, "url": "#" },
            { "title": "全球半导体供应链重塑 多国加大本土芯片投资", "source": "FT中文网", "publish_time": new Date(Date.now() - 720*60000).toISOString(), "significance_score": 6.1, "url": "#" },
            { "title": "联合国报告：全球可再生能源投资首超化石燃料", "source": "AP News", "publish_time": new Date(Date.now() - 900*60000).toISOString(), "significance_score": 5.7, "url": "#" },
        ];
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.NewsManager = new NewsManager();
});
