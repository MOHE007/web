# Render 部署清单（后端与前端）

## 环境变量
- `DEEPSEEK_API_KEY`：用于新闻显著性评分的密钥（务必使用 Render 的 Secret，切勿提交到仓库）。
- `GATEWAY_ALLOW_ORIGINS`：前端跨域白名单，逗号分隔，如 `https://yourdomain.com,http://localhost:3000`。
- `COLLECTOR_URL`：默认 `http://127.0.0.1:8000`。
- `PARSER_URL`：默认 `http://127.0.0.1:8002`。
- `CLEANER_URL`：建议 `http://127.0.0.1:8004`（或按实际服务端口设置）。
- `NEWS_URL`：默认 `http://127.0.0.1:8001`。
- `CATEGORY_URL`：建议 `http://127.0.0.1:8003`（或按实际服务端口设置）。

## 服务端口约定（建议统一）
- `api-gateway`：`8000`
- `news-service`：`8001`
- `parser-service`：`8002`
- `category-service`：`8003`
- `cleaner-service`：`8004`

> 如端口无法调整，请通过上述环境变量在网关内重定向到正确服务地址。

## 新闻导入与评分
- Google News 导入接口：`GET /import/google_news`
  - 参数：
    - `lang`（默认 `en`）
    - `limit`（1..100）
    - `q`（搜索关键词）
    - `include`（逗号分隔类别白名单，如 `technology,world`）
    - `exclude`（逗号分隔类别黑名单，如 `entertainment,sports`，默认即排除娱乐与体育）
    - `score`（布尔，是否导入时自动打分）
- 评分说明：七因子加权，`positivity` 权重仅占总分的 1/20，其余六因子均分 95%。

## 安全建议
- 所有密钥通过 Render Secret 管理；本地开发使用 `export DEEPSEEK_API_KEY=...` 注入，不要写入配置文件。
- 网关仅开放必要路由，CORS 通过环境变量严格限定来源。

本项目采用 FastAPI 微服务架构，建议在 Render 部署后端 Web Service；前端为纯静态，可部署在 GitHub Pages 或 Render Static Site。

## 一键部署清单

### 后端（每个服务创建一个 Web Service）
- 代码路径：
  - `backend/api-gateway`
  - `backend/news-service`
  - `backend/category-service`
  - `backend/parser-service`
  - `backend/cleaner-service`

- Start Command（所有服务通用）：
  - `uvicorn main:app --host 0.0.0.0 --port $PORT`

- 环境变量（网关）：
  - `GATEWAY_ALLOW_ORIGINS`：允许跨域的前端站点，逗号分隔。例如：
    - `https://<your-pages>.github.io,https://<your-static>.onrender.com`
  - `COLLECTOR_URL`：采集服务地址，例如 `https://collector-service.onrender.com`
  - `PARSER_URL`：解析服务地址，例如 `https://parser-service.onrender.com`
  - `CLEANER_URL`：清洗服务地址，例如 `https://cleaner-service.onrender.com`
  - `NEWS_URL`：新闻服务地址，例如 `https://news-service.onrender.com`
  - `CATEGORY_URL`：分类服务地址，例如 `https://category-service.onrender.com`

- 其他服务通常无需额外环境变量（如有数据库配置，请在对应服务添加相关变量）。

### 前端（二选一）
- GitHub Pages：仓库设置 Pages，来源选择 `main` 分支下 `frontend` 目录。
- Render Static Site：新建 Static Site，Root Directory 设为 `frontend`，Publish Directory 填 `frontend`。

- 前端 API 基础地址配置：
  - 在 `frontend/js/api.js` 已默认指向 `https://your-gateway.onrender.com`（占位）。
  - 推荐在 `frontend/index.html` 通过运行时覆盖：
    ```html
    <script>
      window.__API_BASE__ = 'https://your-gateway.onrender.com';
    </script>
    ```

## 验证步骤
- 网关 `GET /health` 返回各服务 `healthy` 或 `degraded`。
- 前端访问首页，`/news` 与 `/categories/tree` 请求不返回 503。

## 常见问题
- 503：某个后端服务未部署或地址未正确配置到网关环境变量。
- CORS 报错：将前端域名加入 `GATEWAY_ALLOW_ORIGINS`，并重新部署网关。