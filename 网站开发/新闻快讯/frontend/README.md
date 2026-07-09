# 瓦卡拉NEWs — 前端

> 极简新闻阅读器 · News Minimalist 风格

纯原生 HTML / CSS / JavaScript 构建，零依赖，零构建步骤。

## 功能

- 📰 **按重要性排序** — 新闻按 AI 评分降序排列
- 🎯 **评分圆点** — 彩色圆点直观显示重要性（灰→黄→绿→蓝→紫）
- 📱 **极简阅读** — 只有标题 + 分数 + 来源 + 时间，没有冗余装饰
- 🌙 **暗色模式** — 跟随系统主题自动切换
- 🔄 **API 静默降级** — 后端不可用时自动使用示例数据

## 项目结构

```
frontend/
├── index.html          # 首页
├── styles/
│   └── main.css        # 样式
├── js/
│   ├── api.js          # API 请求封装
│   ├── news.js         # 新闻渲染与排序
│   └── app.js          # 应用入口
├── assets/             # 静态资源
├── CNAME               # 自定义域名
└── README.md           # 本文件
```

## 快速开始

### 环境要求

- 任意静态文件服务器（Python / Node / VS Code Live Server）
- 现代浏览器

### 启动

```bash
# 方式一：Python（推荐）
cd frontend
python3 -m http.server 3000

# 方式二：Node
npx http-server frontend -p 3000
```

打开浏览器访问 `http://localhost:3000`

### API 配置

在 `index.html` 中通过全局变量覆盖 API 地址：

```html
<script>
  window.__API_BASE__ = 'https://your-api-domain.com';
</script>
```

- 本地开发：自动使用 `http://127.0.0.1:8000`
- 生产环境：默认使用 `https://api.wakolanews.online`

## 部署

### GitHub Pages（推荐）

仓库已配置 GitHub Actions，推送 `main` 分支自动部署。

### 手动部署

任何静态托管平台均可（Vercel / Netlify / Render / 任意 CDN），发布目录指向 `frontend/` 即可。

## 设计理念

借鉴 [News Minimalist](https://www.newsminimalist.com) 的设计哲学：

> **Content first, maximum readability, zero clutter**

- 单列居中布局，max-width 680px
- 每篇新闻只展示：标题 + 评分圆点 + 来源 + 相对时间
- 点击标题直接跳转原文
- 没有分类导航、搜索、分页、广告等无关元素
- 页脚内嵌完整 About 内容，首页即文档

## License

MIT
