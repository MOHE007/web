import schedule
import time
import requests
import yaml
import os

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建 feeds.yml 的绝对路径
feeds_path = os.path.join(current_dir, '..', 'collector-service', 'feeds.yml')

API_GATEWAY_URL = "http://localhost:8000"

def load_feeds():
    """从 feeds.yml 加载新闻源配置"""
    try:
        with open(feeds_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载 feeds.yml 时出错: {e}")
        return {'feeds': []}

def trigger_collection(feed_name, url):
    """触发 API Gateway 的新闻采集流程"""
    print(f"正在触发采集: {feed_name} ({url})")
    try:
        response = requests.post(f"{API_GATEWAY_URL}/process-news", json={"url": url})
        if response.status_code == 200:
            print(f"成功触发采集: {feed_name}")
        else:
            print(f"采集失败 {feed_name}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"请求 API Gateway 时出错: {e}")

def schedule_jobs():
    """根据 feeds.yml 的配置安排采集任务"""
    feeds = load_feeds()
    if not feeds:
        print("无法加载 feeds.yml，调度服务终止")
        return
    
    for feed in feeds:
        feed_name = feed.get('name')
        url = feed.get('url')
        frequency = feed.get('frequency_minutes', 60)
        
        if feed_name and url and frequency:
            schedule.every(frequency).minutes.do(
                trigger_collection, feed_name=feed_name, url=url
            )
            print(f"已安排：{feed_name} 每 {frequency} 分钟采集一次")

def main():
    print("调度服务启动...")
    schedule_jobs()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()