from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import httpx
import asyncio
import os

app = FastAPI()

# CORS 配置（支持环境变量覆盖）
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    # 生产站点域名（前端注入为 https://api.wakolanews.online）
    "https://wakolanews.online",
    "https://api.wakolanews.online",
]
env_origins = os.getenv("GATEWAY_ALLOW_ORIGINS", "").strip()
allow_origins = default_origins
if env_origins:
    # 逗号分隔的域名列表
    allow_origins = [o.strip() for o in env_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 微服务地址配置（支持环境变量覆盖）
SERVICE_URLS = {
    # 注意：collector 不能与网关同端口，改为 8005
    "collector": os.getenv("COLLECTOR_URL", "http://127.0.0.1:8005"),
    "parser": os.getenv("PARSER_URL", "http://127.0.0.1:8002"),
    "cleaner": os.getenv("CLEANER_URL", "http://127.0.0.1:8004"),
    "news": os.getenv("NEWS_URL", "http://127.0.0.1:8001"),
    "category": os.getenv("CATEGORY_URL", "http://127.0.0.1:8003"),
}

class CollectRequest(BaseModel):
    url: str

class ParseRequest(BaseModel):
    content: str
    content_type: str
    url: str

class NewsItem(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    author: Optional[str] = None
    source: str
    url: str

async def call_service(service_name: str, endpoint: str, method: str = "GET", data: dict = None, params: dict = None):
    """调用其他微服务的通用函数"""
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        raise HTTPException(status_code=500, detail=f"Service {service_name} not configured")
    
    url = f"{base_url}{endpoint}"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            if method == "GET":
                response = await client.get(url, params=params, timeout=30.0)
            else:
                response = await client.post(url, json=data, timeout=30.0)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Service {service_name} error: {e.response.text}")

@app.get("/")
def read_root():
    return {"message": "News Processing API Gateway", "version": "1.0.0"}

@app.post("/process-news")
async def process_news(request: CollectRequest):
    """完整的新闻处理流程：收集 -> 解析 -> 清洗"""
    try:
        # 1. 收集数据
        collect_result = await call_service("collector", "/collect", "GET", params={"url": request.url})
        
        if not collect_result.get("success"):
            raise HTTPException(status_code=400, detail="Failed to collect data")
        
        html_content = collect_result.get("content", "")
        
        # 2. 解析数据
        parse_data = {
            "content": html_content,
            "content_type": "html",
            "source_url": request.url
        }
        parse_result = await call_service("parser", "/parse", "POST", data=parse_data)
        
        # 3. 清洗数据
        clean_result = await call_service("cleaner", "/clean", "POST", data=parse_result)
        
        # 4. 自动入库（若非重复）
        saved = False
        saved_item = None
        try:
            if clean_result and not clean_result.get("is_duplicate") and clean_result.get("cleaned_item"):
                # news-service 的创建接口期望字段：title, content, publish_time, author, source, url, category?, tags?
                cleaned_item = clean_result.get("cleaned_item", {})
                create_payload = {
                    "title": cleaned_item.get("title"),
                    "content": cleaned_item.get("content"),
                    "publish_time": cleaned_item.get("publish_time"),
                    "author": cleaned_item.get("author"),
                    "source": cleaned_item.get("source"),
                    "url": cleaned_item.get("url"),
                    # 可选：分类与标签暂不自动推断
                }
                saved_item = await call_service("news", "/news", "POST", data=create_payload)
                saved = True
        except Exception:
            # 入库失败不影响处理流程结果返回
            saved = False
            saved_item = None
        
        return {
            "success": True,
            "data": clean_result,
            "saved": saved,
            "saved_item": saved_item,
            "processing_steps": ["collect", "parse", "clean", "save"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# 新闻服务路由
@app.api_route("/news/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def news_proxy(request: Request, path: str):
    """代理到新闻服务"""
    method = request.method
    data = await request.json() if request.method in ["POST", "PUT"] else None
    params = dict(request.query_params)
    # GET 列表请求的分页与搜索参数映射：page/limit -> skip/limit，search -> keyword
    if method == "GET":
        page = int(params.get("page", "1") or "1")
        limit = int(params.get("limit", "20") or "20")
        if page and page > 1:
            params["skip"] = (page - 1) * limit
        # 始终传递 limit（即便为默认）保证与前端一致
        params["limit"] = limit
        # 重命名搜索参数
        if "search" in params:
            params["keyword"] = params.pop("search")
        # 移除前端分页参数避免后端误识别
        params.pop("page", None)

    # 特例：news-service 中的非 /news 前缀端点需要直通映射
    # /news/import/* -> /import/*, /news/top -> /top, /news/rescore -> /rescore, /news/score/{id} -> /score/{id}
    if path.startswith("import/"):
        return await call_service("news", f"/{path}", method, data=data, params=params)
    if path == "top":
        return await call_service("news", "/top", method, data=data, params=params)
    if path == "rescore":
        return await call_service("news", "/rescore", method, data=data, params=params)
    if path.startswith("score/"):
        return await call_service("news", f"/{path}", method, data=data, params=params)

    return await call_service("news", f"/news/{path}", method, data=data, params=params)

# 兼容根路径 /news 的代理（避免重定向问题）
@app.api_route("/news", methods=["GET", "POST"])
async def news_root_proxy(request: Request):
    method = request.method
    data = await request.json() if request.method == "POST" else None
    params = dict(request.query_params)
    if method == "GET":
        page = int(params.get("page", "1") or "1")
        limit = int(params.get("limit", "20") or "20")
        if page and page > 1:
            params["skip"] = (page - 1) * limit
        params["limit"] = limit
        if "search" in params:
            params["keyword"] = params.pop("search")
        params.pop("page", None)
    return await call_service("news", "/news", method, data=data, params=params)

# 兼容新闻服务的导入与评分等非 /news 前缀端点
@app.get("/news/import/google_news")
async def news_import_google_proxy(request: Request):
    params = dict(request.query_params)
    return await call_service("news", "/import/google_news", "GET", params=params)

@app.get("/news/import/newsminimalist")
async def news_import_minimalist_proxy(request: Request):
    params = dict(request.query_params)
    return await call_service("news", "/import/newsminimalist", "GET", params=params)

@app.get("/news/top")
async def news_top_proxy(request: Request):
    params = dict(request.query_params)
    return await call_service("news", "/top", "GET", params=params)

@app.post("/news/rescore")
async def news_rescore_proxy(request: Request):
    params = dict(request.query_params)
    return await call_service("news", "/rescore", "POST", params=params)

@app.post("/news/score/{news_id}")
async def news_score_proxy(news_id: str):
    return await call_service("news", f"/score/{news_id}", "POST")

# 分类服务路由
@app.api_route("/categories/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def category_proxy(request: Request, path: str):
    """代理到分类服务"""
    method = request.method
    data = await request.json() if request.method in ["POST", "PUT"] else None
    params = dict(request.query_params)
    
    return await call_service("category", f"/categories/{path}", method, data=data, params=params)

# 兼容根路径 /categories 的代理
@app.api_route("/categories", methods=["GET", "POST"])
async def categories_root_proxy(request: Request):
    method = request.method
    data = await request.json() if request.method == "POST" else None
    params = dict(request.query_params)
    return await call_service("category", "/categories", method, data=data, params=params)

@app.get("/health")
async def health_check():
    """健康检查，验证所有服务状态"""
    services_status = {}
    
    for service_name, service_url in SERVICE_URLS.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{service_url}/docs", timeout=5.0)
                services_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_status[service_name] = "unavailable"
    
    overall_status = "healthy" if all(status == "healthy" for status in services_status.values()) else "degraded"
    
    return {
        "status": overall_status,
        "services": services_status,
        "timestamp": "2024-01-15T14:30:00Z"
    }