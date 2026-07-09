# 瓦卡拉NEWs — 属于中国人的极简新闻

> AI 驱动的新闻聚合器，按**重要性**为新闻打分排序，只展示真正值得阅读的新闻。

参考 [News Minimalist](https://www.newsminimalist.com) 的设计理念，面向中文用户打造。

---

## 项目结构

```
.
├── 网站开发/新闻快讯/
│   ├── frontend/                # 前端（纯静态，零构建）
│   │   ├── index.html           # 首页
│   │   ├── styles/main.css      # 样式
│   │   ├── js/
│   │   │   ├── api.js           # API 请求封装
│   │   │   ├── news.js          # 新闻渲染与排序
│   │   │   └── app.js           # 应用入口
│   │   └── CNAME                # 自定义域名
│   ├── backend/
│   │   ├── api-gateway/         # API 网关（入口，端口 8000）
│   │   ├── news-service/        # 新闻 CRUD + 导入 + AI 评分（端口 8001）
│   │   ├── parser-service/      # HTML 解析（端口 8002）
│   │   ├── category-service/    # 分类管理（端口 8003）
│   │   ├── cleaner-service/     # 数据清洗 + 去重（端口 8004）
│   │   ├── collector-service/   # 爬虫采集（端口 8005）
│   │   └── scheduler-service/   # 定时调度
│   ├── render.yaml              # Render Blueprint 一键部署
│   ├── CHANGELOG.md
│   └── docs/策划.md
└── 小程序/                      # 微信小程序（搁置）
```

## 技术栈

| 层次 | 技术 |
|---|---|
| **前端** | 原生 HTML / CSS / JavaScript（零依赖、零构建） |
| **后端** | Python + FastAPI + uvicorn |
| **AI 评分** | DeepSeek API（可配置，未配置时使用启发式评分兜底） |
| **存储** | 内存（后续可升级为 PostgreSQL / Redis） |
| **部署** | Render Blueprint / GitHub Pages |

## 功能特性

### 前端（News Minimalist 极简风格）

- **按重要性排序** — 新闻按 AI 评分降序排列，最重要的在最前
- **评分圆点** — 彩色圆点直观显示重要性（灰→黄→绿→蓝→紫）
- **极简阅读** — 只有标题 + 分数 + 来源 + 时间，没有冗余装饰
- **暗色模式** — 跟随系统主题自动切换
- **响应式** — 桌面和移动端完美适配
- **API 静默降级** — 后端不可用时自动使用示例数据，不报错

### 后端微服务

- **多源采集** — 支持 Google News RSS + News Minimalist 抓取 + 自定义新闻源
- **自动翻译** — 外文标题自动转译为中文（MyMemory API）
- **AI 评分** — DeepSeek 七因子评分（规模、影响、新颖性、潜力、历史意义、正面性、可信度）
- **智能分类** — 基于标题关键词自动归类
- **去重机制** — 按 URL 去重，避免重复新闻

## 快速开始

### 本地启动前端

```bash
# 只需要一个静态服务器
cd "网站开发/新闻快讯/frontend"
python3 -m http.server 3000
# 访问 http://localhost:3000
```

### 本地启动后端

```bash
# 依次启动各微服务（需要 Python 3.x）
cd "网站开发/新闻快讯/backend"

# API 网关
cd api-gateway && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000

# 新闻服务
cd news-service && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8001

# 其他服务同理
```

## 一键部署

### 前端 → GitHub Pages

仓库已配置 GitHub Actions（`.github/workflows/pages.yml`），推送 `main` 分支自动将 `frontend/` 目录部署到 GitHub Pages。

### 后端 → Render

`render.yaml` 定义了完整的 Blueprint，导入仓库即可一键部署 6 个微服务 + 静态站点。

## 新闻源

已配置 12 个新闻源，覆盖中英文主流媒体：

- 🇨🇳 人民网、新华网、腾讯网、网易网
- 🇬🇧 BBC News、纽约时报、路透社、美联社
- 🌍 半岛电视台、德国之声、France 24、中国日报

## License

MIT
