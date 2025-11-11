# Changelog

## 2025-11-12

- API 网关：
  - 新增并修复新闻相关代理路由：
    - `/news/import/google_news` → `news-service:/import/google_news`
    - `/news/import/newsminimalist` → `news-service:/import/newsminimalist`
    - `/news/top`、`/news/rescore`、`/news/score/{id}` 直通至新闻服务对应端点。
  - CORS 默认加入生产域名：`https://wakolanews.online` 与 `https://api.wakolanews.online`。

- 新闻服务：
  - 增加 `POST /news` 创建接口，供 `/process-news` 入库使用。
  - 保留 `/import/google_news` 与 `/import/newsminimalist`；导入时可选 `score=true` 触发显著性评分。
  - 健康检查 `/health` 供网关与前端检测。

- 采集服务：
  - 端口统一为 `8005`；网关默认配置同步到 `COLLECTOR_URL=http://127.0.0.1:8005`。

- 文档：
  - 将 `docs/草案.md` 更名为 `docs/策划.md` 并更新内容（架构、路由、CORS、验证清单）。

### 验证
- 本地：
  - 启动服务后访问 `GET http://127.0.0.1:8000/news` 可获取新闻列表（含样例与导入数据）。
  - 访问 `GET http://127.0.0.1:8000/news/import/google_news?lang=zh&limit=5` 返回导入预览。
- 生产：
  - 设置 `GATEWAY_ALLOW_ORIGINS` 包含前端站点域名。
  - 前端通过 `window.__API_BASE__` 指向 `https://api.wakolanews.online`。