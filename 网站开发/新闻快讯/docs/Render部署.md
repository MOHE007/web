# Render 部署清单（后端与前端）

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