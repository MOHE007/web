# 新闻快讯 - 前端应用

## 项目简介
这是一个基于现代 Web 技术的新闻聚合平台前端应用，采用纯 HTML、CSS 和 JavaScript 构建，无需 Node.js 环境即可运行。

## 功能特性

### 核心功能
- 📰 **新闻浏览**: 支持网格和列表两种视图模式
- 🔍 **智能搜索**: 实时搜索新闻标题和内容
- 📂 **分类导航**: 树形分类结构，支持多级分类
- 🔄 **实时刷新**: 自动和手动刷新新闻数据
- 📱 **响应式设计**: 完美适配移动端和桌面端

### 交互功能
- 🔗 **URL处理**: 支持处理外部新闻URL（采集、解析、清洗）
- 🎯 **新闻详情**: 模态框展示完整新闻内容
- 📊 **热门话题**: 侧边栏展示热门新闻话题
- ⚡ **快速操作**: 浮动操作按钮提供快捷功能

### 用户体验
- 🎨 **现代化UI**: 采用卡片式设计，界面简洁美观
- 🔔 **智能通知**: 操作反馈和错误提示
- ⏱️ **时间显示**: 智能时间格式化（刚刚、几分钟前等）
- 🌓 **深色模式**: 支持深色主题切换（待实现）

## 技术架构

### 前端技术
- **HTML5**: 语义化标签，提升可访问性
- **CSS3**: 现代CSS特性，包括Grid、Flexbox、自定义属性等
- **原生JavaScript**: ES6+语法，模块化开发
- **Font Awesome**: 图标库
- **Google Fonts**: Inter字体

### 架构特点
- **模块化设计**: 代码按功能模块组织
- **事件驱动**: 基于事件的前端架构
- **API封装**: 统一的API请求管理
- **错误处理**: 完善的错误处理和用户反馈

## 项目结构

```
frontend/
├── index.html          # 主页面
├── styles/
│   └── main.css       # 主样式文件
├── js/
│   ├── api.js         # API封装模块
│   ├── news.js        # 新闻管理模块
│   ├── category.js    # 分类管理模块
│   ├── ui.js          # UI管理模块
│   └── app.js         # 主应用模块
└── README.md          # 项目文档
```

## 快速开始

### 环境要求
- Python 3.x（用于启动本地服务器）
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 启动步骤

1. **启动后端服务**（确保所有微服务已运行）
   ```bash
   # API网关 (端口8000)
   cd backend/api-gateway && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
   
   # 新闻服务 (端口8004)
   cd backend/news-service && python3 -m uvicorn main:app --host 0.0.0.0 --port 8004
   
   # 分类服务 (端口8005)
   cd backend/category-service && python3 -m uvicorn main:app --host 0.0.0.0 --port 8005
   ```

2. **启动前端服务器**
   ```bash
   cd frontend
   python3 -m http.server 3000
   ```

3. **访问应用**
   打开浏览器访问: http://localhost:3000

## API 接口

前端应用通过 API 网关与后端服务通信：

### 新闻相关接口
- `GET /news` - 获取新闻列表
- `GET /news/{id}` - 获取新闻详情
- `POST /news` - 创建新闻
- `PUT /news/{id}` - 更新新闻
- `DELETE /news/{id}` - 删除新闻

### 分类相关接口
- `GET /categories` - 获取分类列表
- `GET /categories/tree` - 获取分类树
- `GET /categories/{id}` - 获取分类详情
- `POST /categories` - 创建分类

### 处理接口
- `POST /process-news` - 完整处理新闻URL
- `POST /collect-only` - 仅采集内容
- `POST /parse-only` - 仅解析内容
- `POST /clean-only` - 仅清洗内容

## 开发指南

### 添加新功能

1. **创建新模块**: 在 `js/` 目录下创建新的 JavaScript 文件
2. **注册模块**: 在 `app.js` 中初始化新模块
3. **添加样式**: 在 `main.css` 中添加对应的样式

### 修改API接口

编辑 `js/api.js` 文件，按照现有模式添加新的 API 方法：

```javascript
async newMethod(params) {
    return this.request('/endpoint', {
        method: 'POST',
        body: JSON.stringify(params)
    });
}
```

### 样式定制

应用使用 CSS 自定义属性（变量）进行主题配置，主要变量在 `:root` 选择器中定义：

```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --background-color: #ffffff;
    /* ... 其他变量 */
}
```

## 浏览器兼容性

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## 性能优化

- **代码分割**: 按功能模块组织代码
- **事件委托**: 减少事件监听器数量
- **防抖节流**: 搜索和滚动事件优化
- **懒加载**: 图片和内容懒加载（待实现）

## 待实现功能

- [ ] 深色模式切换
- [ ] 图片懒加载
- [ ] 无限滚动
- [ ] 用户偏好设置
- [ ] 离线缓存
- [ ] PWA支持
- [ ] 国际化支持

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 许可证

MIT License