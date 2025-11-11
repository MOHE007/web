from fastapi import FastAPI
from pydantic import BaseModel
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import json

app = FastAPI()

class ParseRequest(BaseModel):
    content: str
    content_type: str  # html, xml, json
    source_url: str

class NewsData(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    author: Optional[str] = None
    source: str
    url: str

@app.post("/parse", response_model=NewsData)
def parse_data(request: ParseRequest):
    """解析不同格式的新闻数据"""
    try:
        if request.content_type == "html":
            return parse_html(request.content, request.source_url)
        elif request.content_type == "json":
            return parse_json(request.content, request.source_url)
        elif request.content_type == "xml":
            return parse_xml(request.content, request.source_url)
        else:
            return NewsData(source=request.source_url, url=request.source_url)
    except Exception as e:
        return NewsData(source=request.source_url, url=request.source_url)

def parse_html(content: str, source_url: str) -> NewsData:
    """解析HTML格式的新闻"""
    soup = BeautifulSoup(content, 'html.parser')
    
    # 提取标题
    title = None
    if soup.title:
        title = soup.title.string
    
    # 提取正文内容
    content_text = None
    # 尝试常见的正文选择器
    content_selectors = ['article', '.content', '.article-content', '#content', '.news-content']
    for selector in content_selectors:
        element = soup.select_one(selector)
        if element:
            content_text = element.get_text(strip=True)
            break
    
    # 提取发布时间
    publish_time = None
    time_selectors = ['time', '.publish-time', '.date', '.pub-time']
    for selector in time_selectors:
        element = soup.select_one(selector)
        if element:
            publish_time = element.get_text(strip=True)
            break
    
    return NewsData(
        title=title,
        content=content_text,
        publish_time=publish_time,
        source=source_url,
        url=source_url
    )

def parse_json(content: str, source_url: str) -> NewsData:
    """解析JSON格式的新闻数据"""
    try:
        data = json.loads(content)
        return NewsData(
            title=data.get('title'),
            content=data.get('content'),
            publish_time=data.get('publish_time'),
            author=data.get('author'),
            source=source_url,
            url=source_url
        )
    except json.JSONDecodeError:
        return NewsData(source=source_url, url=source_url)

def parse_xml(content: str, source_url: str) -> NewsData:
    """解析XML格式的新闻数据"""
    soup = BeautifulSoup(content, 'xml')
    
    title = None
    content_text = None
    publish_time = None
    author = None
    
    # 尝试提取XML中的常见新闻字段
    title_elem = soup.find('title')
    if title_elem:
        title = title_elem.text
    
    content_elem = soup.find('content') or soup.find('body')
    if content_elem:
        content_text = content_elem.text
    
    time_elem = soup.find('pubDate') or soup.find('publish_time') or soup.find('date')
    if time_elem:
        publish_time = time_elem.text
    
    author_elem = soup.find('author') or soup.find('creator')
    if author_elem:
        author = author_elem.text
    
    return NewsData(
        title=title,
        content=content_text,
        publish_time=publish_time,
        author=author,
        source=source_url,
        url=source_url
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)