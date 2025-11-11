from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import uuid

app = FastAPI()

# 数据模型
class NewsItem(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    author: Optional[str] = None
    source: str
    url: str
    category: Optional[str] = None
    tags: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class NewsCreate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    author: Optional[str] = None
    source: str
    url: str
    category: Optional[str] = None
    tags: List[str] = []

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None

# 简单的内存存储（生产环境应该使用数据库）
news_storage = {}

# 初始化一些测试数据
sample_news = [
    {
        "id": "1",
        "title": "百度发布新AI产品",
        "content": "百度公司今日发布了最新的人工智能产品，引起了业界广泛关注。",
        "publish_time": "2024-01-15 10:00:00",
        "author": "张三",
        "source": "baidu.com",
        "url": "https://www.baidu.com/news/1",
        "category": "科技",
        "tags": ["AI", "百度", "人工智能"],
        "created_at": "2024-01-15 10:00:00",
        "updated_at": "2024-01-15 10:00:00"
    },
    {
        "id": "2", 
        "title": "科技行业迎来新突破",
        "content": "最新研究显示，科技行业在人工智能领域取得了重大突破。",
        "publish_time": "2024-01-14 15:30:00",
        "author": "李四",
        "source": "tech.sina.com",
        "url": "https://tech.sina.com/news/2",
        "category": "科技",
        "tags": ["科技", "突破", "AI"],
        "created_at": "2024-01-14 15:30:00",
        "updated_at": "2024-01-14 15:30:00"
    }
]

# 添加测试数据
for news in sample_news:
    news_storage[news["id"]] = news

@app.get("/")
def read_root():
    return {"message": "News Service API", "version": "1.0.0"}

@app.post("/news", response_model=NewsItem)
def create_news(news: NewsCreate):
    """创建新闻"""
    news_id = str(uuid.uuid4())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    news_item = NewsItem(
        id=news_id,
        **news.dict(),
        created_at=now,
        updated_at=now
    )
    
    news_storage[news_id] = news_item.dict()
    return news_item

@app.get("/news/{news_id}", response_model=NewsItem)
def get_news(news_id: str):
    """获取单条新闻"""
    if news_id not in news_storage:
        raise HTTPException(status_code=404, detail="News not found")
    
    return NewsItem(**news_storage[news_id])

@app.get("/news", response_model=List[NewsItem])
def list_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    source: Optional[str] = None,
    keyword: Optional[str] = None
):
    """获取新闻列表，支持分页和筛选"""
    news_list = list(news_storage.values())
    
    # 应用筛选条件
    if category:
        news_list = [n for n in news_list if n.get("category") == category]
    
    if source:
        news_list = [n for n in news_list if n.get("source") == source]
    
    if keyword:
        keyword = keyword.lower()
        news_list = [
            n for n in news_list 
            if (keyword in n.get("title", "").lower() or 
                keyword in n.get("content", "").lower())
        ]
    
    # 按发布时间排序（最新的在前）
    news_list.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
    
    # 分页
    total = len(news_list)
    news_list = news_list[skip:skip + limit]
    
    return [NewsItem(**news) for news in news_list]

@app.put("/news/{news_id}", response_model=NewsItem)
def update_news(news_id: str, news_update: NewsUpdate):
    """更新新闻"""
    if news_id not in news_storage:
        raise HTTPException(status_code=404, detail="News not found")
    
    existing_news = news_storage[news_id]
    update_data = news_update.dict(exclude_unset=True)
    
    # 更新时间戳
    update_data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 更新新闻数据
    existing_news.update(update_data)
    news_storage[news_id] = existing_news
    
    return NewsItem(**existing_news)

@app.delete("/news/{news_id}")
def delete_news(news_id: str):
    """删除新闻"""
    if news_id not in news_storage:
        raise HTTPException(status_code=404, detail="News not found")
    
    del news_storage[news_id]
    return {"message": "News deleted successfully"}

@app.get("/stats")
def get_stats():
    """获取统计信息"""
    news_list = list(news_storage.values())
    
    stats = {
        "total_news": len(news_list),
        "categories": {},
        "sources": {},
        "latest_news": None
    }
    
    # 统计分类
    for news in news_list:
        category = news.get("category", "未分类")
        stats["categories"][category] = stats["categories"].get(category, 0) + 1
        
        source = news.get("source", "未知")
        stats["sources"][source] = stats["sources"].get(source, 0) + 1
    
    # 获取最新新闻
    if news_list:
        latest = max(news_list, key=lambda x: x.get("publish_time", ""))
        stats["latest_news"] = {
            "title": latest.get("title"),
            "publish_time": latest.get("publish_time")
        }
    
    return stats

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "news", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)