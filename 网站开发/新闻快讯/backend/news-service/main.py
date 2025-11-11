from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import asyncio
import os
import json
import urllib.parse

# 外部依赖：抓取与解析、翻译
import httpx
from bs4 import BeautifulSoup

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
    language: Optional[str] = None
    significance_score: Optional[float] = None
    significance_factors: Optional[Dict[str, float]] = None
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
    language: Optional[str] = None
    significance_score: Optional[float] = None
    significance_factors: Optional[Dict[str, float]] = None

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

# 翻译工具：将文本转译为中文
async def translate_to_zh(text: Optional[str], source_lang: Optional[str] = None) -> Optional[str]:
    """使用 MyMemory API 将文本转译为中文。
    注意：免费接口存在速率限制，必要时可改为付费翻译服务。
    """
    if not text:
        return text
    api = "https://api.mymemory.translated.net/get"
    src = (source_lang or "en").lower()
    params = {"q": text, "langpair": f"{src}|zh-CN"}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            r = await client.get(api, params=params)
            r.raise_for_status()
            data = r.json()
            translated = (
                data.get("responseData", {}).get("translatedText")
                or text
            )
            return translated
    except Exception:
        return text

# 抓取 News Minimalist 首页，提取新闻标题与链接
async def fetch_newsminimalist(limit: int = 20) -> List[dict]:
    url = "https://www.newsminimalist.com"
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        resp = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; NewsService/1.0; +https://www.wakolanews.online)"
        })
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    items: List[dict] = []
    # 策略：抓取页面中的高质 a 标签（有文字且是外链/站内链接），作为新闻条目
    # 由于站点结构可能更新，这里采用通用解析策略，后续可按具体 DOM 优化
    anchors = soup.find_all("a")
    for a in anchors:
        title = (a.get_text() or "").strip()
        href = a.get("href") or ""
        if not title or not href:
            continue
        if href.startswith("#"):
            continue
        # 过滤导航与无关链接：长度阈值 + 去除明显的导航文字
        if len(title) < 8:
            continue
        if title.lower() in {"home", "about", "contact", "privacy", "terms"}:
            continue

        # 归一化 URL（相对链接 -> 绝对链接）
        if href.startswith("/"):
            href = url.rstrip("/") + href

        # 翻译标题为中文
        title_zh = await translate_to_zh(title, source_lang="en")

        item = {
            "title": title_zh or title,
            "content": None,
            "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "author": None,
            "source": "newsminimalist.com",
            "url": href,
            "category": "综合",
            "tags": [],
            "language": "en"
        }
        items.append(item)
        if len(items) >= limit:
            break

    return items

# 基于 Google News RSS 的多语言抓取
LANG_FEEDS = {
    "en": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "ar": "https://news.google.com/rss?hl=ar&gl=AE&ceid=AE:ar",
    "zh": "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "fr": "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr",
    "de": "https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de",
    "el": "https://news.google.com/rss?hl=el&gl=GR&ceid=GR:el",
    "hi": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "it": "https://news.google.com/rss?hl=it&gl=IT&ceid=IT:it",
    "ru": "https://news.google.com/rss?hl=ru&gl=RU&ceid=RU:ru",
    "es": "https://news.google.com/rss?hl=es&gl=ES&ceid=ES:es",
    "sv": "https://news.google.com/rss?hl=sv&gl=SE&ceid=SE:sv",
    "uk": "https://news.google.com/rss?hl=uk&gl=UA&ceid=UA:uk",
}

def _categorize_title(title: str) -> str:
    t = (title or "").lower()
    # 简单关键词映射分类
    categories = {
        "sports": ["sports", "football", "soccer", "nba", "mlb", "f1", "tennis", "体育", "世界杯"],
        "entertainment": ["entertainment", "celebrity", "movie", "film", "hollywood", "音乐", "电影", "明星", "娱乐"],
        "technology": ["tech", "technology", "ai", "artificial intelligence", "quantum", "software", "semiconductor", "芯片", "人工智能", "科技"],
        "business": ["business", "economy", "market", "gdp", "inflation", "央行", "商业", "经济", "股市", "通胀"],
        "politics": ["politics", "election", "government", "policy", "立法", "选举", "政府", "政策", "政治"],
        "world": ["world", "global", "international", "国际", "全球", "世界"],
        "finance": ["finance", "stocks", "bonds", "invest", "投资", "金融"],
    }
    for cat, keys in categories.items():
        for k in keys:
            if k in t:
                return cat
    return "综合"

async def fetch_google_news(lang: str = "en", limit: int = 20, q: Optional[str] = None, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> List[dict]:
    base = LANG_FEEDS.get(lang, LANG_FEEDS["en"])
    # Google News 搜索需要 /rss/search
    url = base if not q else base.replace("/rss", "/rss/search") + ("&q=" + urllib.parse.quote_plus(q))
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (NewsService)"})
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "xml")
    items: List[dict] = []
    for item in soup.find_all("item"):
        title = (item.find("title").get_text() if item.find("title") else "").strip()
        link = (item.find("link").get_text() if item.find("link") else "").strip()
        if not title or not link:
            continue
        title_zh = await translate_to_zh(title, source_lang=lang)
        category = _categorize_title(title)
        # 过滤逻辑：优先 include（如存在），其次 exclude；默认排除娱乐、体育
        exclude_set = set((exclude or ["entertainment", "sports"]))
        include_set = set(include or [])
        if include_set and category not in include_set:
            continue
        if category in exclude_set:
            continue
        items.append({
            "title": title_zh or title,
            "content": None,
            "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "author": None,
            "source": "news.google.com",
            "url": link,
            "category": category,
            "tags": [],
            "language": lang
        })
        if len(items) >= limit:
            break
    return items

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

@app.get("/import/newsminimalist")
async def import_newsminimalist(limit: int = Query(20, ge=1, le=100)):
    """抓取 https://www.newsminimalist.com 并将新闻转译为中文后导入存储。
    返回导入条数与部分预览。
    """
    try:
        items = await fetch_newsminimalist(limit=limit)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Fetch error: {str(e)}")

    # 去重：按 URL 作为唯一键
    existing_urls = {n.get("url") for n in news_storage.values()}
    imported = []
    for n in items:
        if n["url"] in existing_urls:
            continue
        news_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "id": news_id,
            **n,
            "created_at": now,
            "updated_at": now
        }
        news_storage[news_id] = record
        imported.append(record)

    return {
        "imported_count": len(imported),
        "source": "https://www.newsminimalist.com",
        "preview": [{"title": r.get("title"), "url": r.get("url")} for r in imported[:5]]
    }

@app.get("/import/google_news")
async def import_google_news(
    lang: str = Query("en"),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    score: bool = Query(False),
    include: Optional[str] = Query(None, description="逗号分隔的类别白名单，如 technology,world"),
    exclude: Optional[str] = Query(None, description="逗号分隔的类别黑名单，如 entertainment,sports")
):
    """从 Google News RSS 抓取指定语言的新闻，标题转译为中文并入库。"""
    try:
        include_list = [s.strip() for s in (include or "").split(",") if s.strip()] or None
        exclude_list = [s.strip() for s in (exclude or "").split(",") if s.strip()] or None
        items = await fetch_google_news(lang=lang, limit=limit, q=q, include=include_list, exclude=exclude_list)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Fetch error: {str(e)}")

    existing_urls = {n.get("url") for n in news_storage.values()}
    imported = []
    for n in items:
        if n["url"] in existing_urls:
            continue
        news_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {"id": news_id, **n, "created_at": now, "updated_at": now}
        # 可选：导入时立即评分
        if score:
            try:
                res = await deepseek_score_news(record.get("title", ""), record.get("content"), record.get("language"))
                record["significance_score"] = res.get("score")
                record["significance_factors"] = {k: v for k, v in res.items() if k != "score"}
                record["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        news_storage[news_id] = record
        imported.append(record)
    return {
        "imported_count": len(imported),
        "source": f"google_news:{lang}",
        "preview": [{"title": r.get("title"), "url": r.get("url"), "score": r.get("significance_score")} for r in imported[:5]]
    }

# ===== DeepSeek 评分集成 =====
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

async def deepseek_score_news(title: str, content: Optional[str] = None, language: Optional[str] = None) -> Dict[str, float]:
    """调用 DeepSeek Chat Completions 为新闻计算七因子与显著性分数（0-10）。
    因子：scale, impact, novelty, potential, legacy, positivity, credibility。
    positivity 权重为 1/20。
    返回：{"score": float, **factors}
    """
    # 如果未配置 API Key，使用启发式本地打分作为回退方案
    if not DEEPSEEK_API_KEY:
        text = f"{title} {content or ''}"
        tl = text.lower()
        # 关键词集合
        global_keys = ["un","nato","world","global","economy","government","china","united states","us","europe","eu","央行","经济","政府","中国","美国","欧洲","联合国","战争","冲突","地震","疫情"]
        impact_keys = ["sanction","ban","policy","law","death","market","gdp","interest rate","通胀","裁员","股市","政策","法律"]
        novelty_keys = ["breakthrough","new","first","首次","新","突破"]
        potential_keys = ["could","may","potential","可能","潜力","ai","quantum","fusion","gen ai","人工智能"]
        legacy_keys = ["historic","milestone","anniversary","历史性","里程碑","周年"]
        pos_words = ["growth","win","improve","increase","agreement","peace","增长","改善","提高","协议","和平"]
        neg_words = ["crisis","war","conflict","decline","layoff","死亡","危机","战争","冲突","下滑","裁员"]
        credible_domains = ["nytimes","bbc","reuters","ft.com","apnews","washingtonpost","economist","aljazeera","cnbc","bloomberg","wsj"]

        def score_from(keys: List[str], base: float = 5.0, step: float = 1.5, cap: float = 10.0) -> float:
            s = base
            hits = sum(1 for k in keys if k in tl)
            s += min(hits, 3) * step
            return min(cap, s)

        scale = score_from(global_keys)
        impact = score_from(impact_keys)
        novelty = score_from(novelty_keys, step=1.2)
        potential = score_from(potential_keys, step=1.2)
        legacy = score_from(legacy_keys, base=4.0, step=1.5)
        # 情绪：正负词计数映射到 [0,10]
        pos_hits = sum(1 for w in pos_words if w in tl)
        neg_hits = sum(1 for w in neg_words if w in tl)
        positivity = max(0.0, min(10.0, 5.0 + (pos_hits - neg_hits) * 1.5))
        # 可信度根据来源域名
        src = (content or "")
        cred = 5.0
        for d in credible_domains:
            if d in tl:
                cred = 8.0
                break
        credibility = cred
        # 加权总分（positivity 权重 1/20，其余因子均分 95%）
        w_pos = 0.05
        w_other = 0.95 / 6.0
        computed_score = (
            w_other * scale + w_other * impact + w_other * novelty + w_other * potential + w_other * legacy + w_other * credibility + w_pos * positivity
        )
        return {
            "scale": round(scale, 3),
            "impact": round(impact, 3),
            "novelty": round(novelty, 3),
            "potential": round(potential, 3),
            "legacy": round(legacy, 3),
            "positivity": round(positivity, 3),
            "credibility": round(credibility, 3),
            "score": round(computed_score, 3),
        }

    system_prompt = (
        "You are a news significance rater."
        " Score the given news on seven factors: scale, impact, novelty, potential, legacy, positivity, credibility."
        " Each factor MUST be a float in [0,10]."
        " Then combine into a single significance score in [0,10], where positivity has weight 1/20 versus other factors."
        " Output STRICT JSON with keys: scale, impact, novelty, potential, legacy, positivity, credibility, score."
    )
    user_content = {
        "title": title,
        "content": content or "",
        "language": language or "en"
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)}
        ],
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        r = await client.post(f"{DEEPSEEK_API_URL}/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        content_text = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            result = json.loads(content_text)
        except Exception:
            result = {"score": 0.0, "scale": 0.0, "impact": 0.0, "novelty": 0.0, "potential": 0.0, "legacy": 0.0, "positivity": 5.0, "credibility": 5.0}
        def clamp(x):
            try:
                return max(0.0, min(10.0, float(x)))
            except Exception:
                return 0.0
        result = {
            "scale": clamp(result.get("scale")),
            "impact": clamp(result.get("impact")),
            "novelty": clamp(result.get("novelty")),
            "potential": clamp(result.get("potential")),
            "legacy": clamp(result.get("legacy")),
            "positivity": clamp(result.get("positivity")),
            "credibility": clamp(result.get("credibility")),
        }
        # 计算显著性分数：positivity 权重为总分的 1/20，其余六因子均分 95%
        w_pos = 0.05
        w_other = 0.95 / 6.0
        computed_score = (
            w_other * result["scale"] +
            w_other * result["impact"] +
            w_other * result["novelty"] +
            w_other * result["potential"] +
            w_other * result["legacy"] +
            w_other * result["credibility"] +
            w_pos * result["positivity"]
        )
        result["score"] = round(computed_score, 3)
        return result

@app.post("/score/{news_id}")
async def score_single_news(news_id: str):
    if news_id not in news_storage:
        raise HTTPException(status_code=404, detail="News not found")
    n = news_storage[news_id]
    try:
        res = await deepseek_score_news(n.get("title", ""), n.get("content"), n.get("language"))
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"DeepSeek call error: {str(e)}")
    except HTTPException:
        raise
    n["significance_score"] = res.get("score")
    n["significance_factors"] = {k: v for k, v in res.items() if k != "score"}
    n["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    news_storage[news_id] = n
    return {"id": news_id, "score": n["significance_score"], "factors": n["significance_factors"]}

@app.post("/rescore")
async def rescore_all(limit: int = Query(20, ge=1, le=200)):
    ids = list(news_storage.keys())[:limit]
    updated = []
    for nid in ids:
        try:
            res = await score_single_news(nid)
            updated.append(res)
        except Exception:
            continue
    return {"rescored": len(updated), "items": updated}

@app.get("/top")
def list_top(min_score: float = Query(5.0, ge=0.0, le=10.0), limit: int = Query(10, ge=1, le=100)):
    items = [n for n in news_storage.values() if n.get("significance_score", 0.0) >= min_score]
    items.sort(key=lambda x: x.get("significance_score", 0.0), reverse=True)
    items = items[:limit]
    return [NewsItem(**n) for n in items]

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