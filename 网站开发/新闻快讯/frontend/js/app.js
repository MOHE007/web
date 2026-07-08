// 瓦卡拉NEWs — 主应用入口
class WakaNewsApp {
    constructor() {
        console.log('瓦卡拉NEWs 已启动');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new WakaNewsApp();
});
