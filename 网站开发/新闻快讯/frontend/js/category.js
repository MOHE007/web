// 分类管理类
class CategoryManager {
    constructor() {
        this.categories = [];
        this.currentCategory = 'all';
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCategories();
    }

    bindEvents() {
        // 分类树点击事件
        document.getElementById('categoryTree').addEventListener('click', (e) => {
            const item = e.target.closest('.tree-item');
            if (item) {
                const category = item.dataset.category;
                this.selectCategory(category);
            }
        });
    }

    async loadCategories() {
        if (!window.API) {
            setTimeout(() => this.loadCategories(), 100);
            return;
        }
        try {
            const categories = await window.API.getCategoryTree();
            this.categories = categories;
            this.renderCategoryTree();
        } catch (error) {
            console.error('加载分类失败:', error);
        }
    }

    renderCategoryTree() {
        const container = document.getElementById('categoryTree');
        
        const renderTree = (items, level = 0) => {
            return items.map(item => `
                <div class="tree-item ${level > 0 ? 'tree-indent' : ''}" 
                     data-category="${item.name}"
                     style="padding-left: ${12 + level * 16}px">
                    <i class="fas fa-${level === 0 ? 'folder' : 'file'}"></i>
                    <span>${item.name}</span>
                    ${item.children && item.children.length > 0 ? `(${item.children.length})` : ''}
                </div>
                ${item.children ? renderTree(item.children, level + 1) : ''}
            `).join('');
        };

        container.innerHTML = renderTree(this.categories);
        
        // 设置当前选中的分类
        this.updateCategorySelection();
    }

    selectCategory(category) {
        this.currentCategory = category;
        this.updateCategorySelection();
        
        // 触发新闻加载
        if (window.NewsManager) {
            window.NewsManager.switchCategory(category);
        }
    }

    updateCategorySelection() {
        document.querySelectorAll('.tree-item').forEach(item => {
            item.classList.toggle('active', item.dataset.category === this.currentCategory);
        });
    }

    getCategoryName(categoryId) {
        const findCategory = (items) => {
            for (let item of items) {
                if (item.id === categoryId) return item.name;
                if (item.children) {
                    const found = findCategory(item.children);
                    if (found) return found;
                }
            }
            return null;
        };
        
        return findCategory(this.categories);
    }

    getCategoryHierarchy(categoryName) {
        const findPath = (items, path = []) => {
            for (let item of items) {
                const currentPath = [...path, item.name];
                if (item.name === categoryName) return currentPath;
                
                if (item.children) {
                    const found = findPath(item.children, currentPath);
                    if (found) return found;
                }
            }
            return null;
        };
        
        return findPath(this.categories);
    }
}

// 创建分类管理器实例
document.addEventListener('DOMContentLoaded', () => {
    window.CategoryManager = new CategoryManager();
});