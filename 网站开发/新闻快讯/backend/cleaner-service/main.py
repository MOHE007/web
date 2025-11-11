from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import hashlib
from datetime import datetime

app = FastAPI()

class NewsItem(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_time: Optional[str] = None
    author: Optional[str] = None
    source: str
    url: str

class CleanResult(BaseModel):
    cleaned_item: Optional[NewsItem] = None
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

# 简单的内存去重存储（生产环境应该使用Redis等）
deduplication_store = {}

def generate_content_hash(content: str) -> str:
    """生成内容哈希用于去重"""
    if not content:
        return ""
    return hashlib.md5(content.encode()).hexdigest()

def clean_text(text: str) -> str:
    """清洗文本内容"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = ' '.join(text.split())
    
    # 移除特殊字符（保留中文、英文、数字和基本标点）
    import re
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?;:"()\-]', '', text)
    
    return text.strip()

def validate_publish_time(time_str: str) -> Optional[str]:
    """验证和标准化发布时间"""
    if not time_str:
        return None
    
    # 尝试多种时间格式
    time_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y'
    ]
    
    for fmt in time_formats:
        try:
            parsed_time = datetime.strptime(time_str.strip(), fmt)
            return parsed_time.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    
    return None

@app.post("/clean", response_model=CleanResult)
def clean_data(item: NewsItem):
    """清洗新闻数据并去重"""
    
    # 清洗内容
    cleaned_item = NewsItem(
        title=clean_text(item.title) if item.title else None,
        content=clean_text(item.content) if item.content else None,
        publish_time=validate_publish_time(item.publish_time),
        author=clean_text(item.author) if item.author else None,
        source=item.source,
        url=item.url
    )
    
    # 生成内容哈希用于去重
    content_hash = generate_content_hash(cleaned_item.content or "")
    
    # 检查是否重复
    if content_hash and content_hash in deduplication_store:
        return CleanResult(
            cleaned_item=None,
            is_duplicate=True,
            duplicate_of=deduplication_store[content_hash]
        )
    
    # 存储哈希（使用URL作为标识）
    if content_hash:
        deduplication_store[content_hash] = item.url
    
    return CleanResult(
        cleaned_item=cleaned_item,
        is_duplicate=False,
        duplicate_of=None
    )

@app.get("/stats")
def get_cleaning_stats():
    """获取清洗统计信息"""
    return {
        "total_processed": len(deduplication_store),
        "unique_items": len(set(deduplication_store.values())),
        "duplicates_found": 0  # 这里可以添加更详细的统计
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)