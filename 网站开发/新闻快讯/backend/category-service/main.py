from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI()

# 数据模型
class Category(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None

# 简单的内存存储（生产环境应该使用数据库）
category_storage = {}

# 初始化一些测试数据
sample_categories = [
    {"id": "1", "name": "科技", "description": "关于科学技术的最新新闻"},
    {"id": "2", "name": "财经", "description": "金融、市场和商业相关新闻"},
    {"id": "3", "name": "体育", "description": "体育赛事和相关报道"},
    {"id": "4", "name": "娱乐", "description": "电影、音乐、明星等娱乐新闻"},
    {"id": "5", "name": "人工智能", "description": "人工智能领域的进展", "parent_id": "1"},
    {"id": "6", "name": "区块链", "description": "区块链技术和加密货币", "parent_id": "1"}
]

# 添加测试数据
for category in sample_categories:
    category_storage[category["id"]] = category

@app.get("/")
def read_root():
    return {"message": "Category Service API", "version": "1.0.0"}

@app.post("/categories", response_model=Category)
def create_category(category: CategoryCreate):
    """创建分类"""
    category_id = str(uuid.uuid4())
    
    category_item = Category(
        id=category_id,
        **category.dict()
    )
    
    category_storage[category_id] = category_item.dict()
    return category_item

@app.get("/categories/tree")
def get_category_tree():
    """获取分类树"""
    nodes = {}
    
    # 创建节点
    for cat_id, cat_data in category_storage.items():
        nodes[cat_id] = {"id": cat_id, "name": cat_data["name"], "children": []}
    
    # 构建树
    tree = []
    for cat_id, cat_data in category_storage.items():
        parent_id = cat_data.get("parent_id")
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(nodes[cat_id])
        else:
            tree.append(nodes[cat_id])
            
    return tree

@app.get("/categories/{category_id}", response_model=Category)
def get_category(category_id: str):
    """获取单个分类"""
    if category_id not in category_storage:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return Category(**category_storage[category_id])

@app.get("/categories", response_model=List[Category])
def list_categories(parent_id: Optional[str] = None):
    """获取分类列表，支持按父分类筛选"""
    category_list = list(category_storage.values())
    
    if parent_id:
        category_list = [c for c in category_list if c.get("parent_id") == parent_id]
    
    return [Category(**category) for category in category_list]

@app.put("/categories/{category_id}", response_model=Category)
def update_category(category_id: str, category_update: CategoryUpdate):
    """更新分类"""
    if category_id not in category_storage:
        raise HTTPException(status_code=404, detail="Category not found")
    
    existing_category = category_storage[category_id]
    update_data = category_update.dict(exclude_unset=True)
    
    existing_category.update(update_data)
    category_storage[category_id] = existing_category
    
    return Category(**existing_category)

@app.delete("/categories/{category_id}")
def delete_category(category_id: str):
    """删除分类"""
    if category_id not in category_storage:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 检查是否有子分类
    for category in category_storage.values():
        if category.get("parent_id") == category_id:
            raise HTTPException(status_code=400, detail="Cannot delete category with children")
    
    del category_storage[category_id]
    return {"message": "Category deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)